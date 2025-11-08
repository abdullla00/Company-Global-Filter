from __future__ import unicode_literals

from typing import Dict, Optional

import frappe
from frappe import _
from frappe.desk.search import search_link

from company_global_filter.constants import (
    CACHE_KEY_COMPANY_FIELD,
    CACHE_KEY_COMPANY_FIELD_NAME,
    CACHE_KEY_USER_COMPANY,
    CACHE_TTL,
    COMPANY_FIELD_NAME,
    COMPANY_FIELD_OPTIONS,
    COMPANY_FIELD_TYPE,
    CUSTOM_COMPANY_FIELD_NAME,
    IGNORE_DOCTYPES,
    LOG_CATEGORY_DEBUG,
    SYSTEM_DOCTYPES,
)
from company_global_filter.doctype.company_global_filter_settings.company_global_filter_settings import (
    can_user_bypass,
    get_excluded_companies_for_user,
    is_doctype_excluded,
    is_filtering_enabled,
)


@frappe.whitelist()
def get_company_list() -> list:
    """
    Get list of all companies accessible to the current user

    Returns:
        List of company names
    """
    companies = search_link(
        txt="", doctype="Company", reference_doctype="", page_length=100000
    )
    company_names = [c.get("value") for c in companies]
    return company_names


def get_permission_query_conditions(user: str, doctype: Optional[str] = None) -> str:
    """
    Apply global company filter to all doctypes that have a company field
    This function is called by Frappe's permission system

    Args:
        user: Username (required by Frappe hook signature)
        doctype: Name of the doctype to filter (optional)

    Returns:
        SQL condition string to filter by company, or empty string if no filter needed
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    try:
        # Handle both calling patterns
        if doctype is None:
            return ""

        # Check if filtering is enabled
        if not is_filtering_enabled():
            return ""

        # Check if user can bypass filtering
        if can_user_bypass(user):
            logger.debug(f"User {user} can bypass filtering for {doctype}")
            return ""

        # Skip system doctypes that should never be filtered
        if doctype in SYSTEM_DOCTYPES:
            return ""

        # Check if doctype is excluded in settings
        if is_doctype_excluded(doctype):
            logger.debug(f"DocType {doctype} is excluded from filtering")
            return ""

        # Check if session is available (avoid boot errors)
        if not hasattr(frappe, "session") or not frappe.session:
            return ""

        # Check if database is available
        if not hasattr(frappe, "db") or not frappe.db:
            return ""

        # Get user's selected/default company
        user_company = get_user_company()

        if not user_company:
            logger.debug(
                f"No company found for user {user}, skipping filter for {doctype}"
            )
            return ""

        # Check if this doctype has a company field
        company_field_name = get_company_field_name(doctype)

        if not company_field_name:
            return ""

        # Get excluded companies for this user and doctype
        excluded_companies = get_excluded_companies_for_user(user, doctype)

        # Build SQL condition
        # Use parameterized query to prevent SQL injection
        escaped_company = frappe.db.escape(user_company)

        if excluded_companies:
            # Include excluded companies in the condition
            excluded_companies_escaped = [
                frappe.db.escape(c) for c in excluded_companies
            ]
            excluded_companies_str = ", ".join(excluded_companies_escaped)
            condition = f"(`tab{doctype}`.`{company_field_name}` = {escaped_company} OR `tab{doctype}`.`{company_field_name}` IN ({excluded_companies_str}))"
            logger.debug(
                f"Applying company filter for {doctype} with excluded companies: {condition}"
            )
        else:
            # Standard condition without excluded companies
            condition = f"`tab{doctype}`.`{company_field_name}` = {escaped_company}"
            logger.debug(f"Applying company filter for {doctype}: {condition}")

        return condition

    except Exception as e:
        logger = frappe.logger("company_global_filter", allow_site=True)
        logger.warning(
            f"Error in get_permission_query_conditions for {doctype}: {str(e)}",
            exc_info=True,
        )
        # Don't raise errors during permission queries to avoid boot failures
        return ""


def get_user_company() -> Optional[str]:
    """
    Get user's selected company from session or default
    Uses caching to improve performance

    Returns:
        Company name if found, None otherwise
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    try:
        # Check if session is available
        if not hasattr(frappe, "session") or not frappe.session:
            return None

        user = frappe.session.user

        # Check cache first
        cache_key = CACHE_KEY_USER_COMPANY.format(user=user)
        cached_result = frappe.cache().get(cache_key)
        if cached_result is not None:
            return cached_result

        # First check if user has selected a company in session
        selected_company = frappe.session.get("selected_company")

        if selected_company:
            # Cache the result
            frappe.cache().set(cache_key, selected_company, expires_in_sec=CACHE_TTL)
            return selected_company

        # Check if defaults module is available
        if not hasattr(frappe, "defaults"):
            return None

        # Fallback to user's default company
        default_company = frappe.defaults.get_user_default("Company")

        if default_company:
            # Cache the result
            frappe.cache().set(cache_key, default_company, expires_in_sec=CACHE_TTL)
            return default_company

        # If no default, get first available company user has access to
        if hasattr(frappe, "get_list"):
            companies = frappe.get_list("Company", fields=["name"], limit=1)

            if companies:
                company_name = companies[0].name
                # Cache the result
                frappe.cache().set(cache_key, company_name, expires_in_sec=CACHE_TTL)
                return company_name

        return None

    except Exception as e:
        logger = frappe.logger("company_global_filter", allow_site=True)
        logger.warning(f"Error getting user company: {str(e)}", exc_info=True)
        # Don't raise errors during session boot
        return None


def get_company_field_name(doctype: str) -> Optional[str]:
    """
    Check if doctype has a company field and return the field name
    Uses caching to improve performance

    Args:
        doctype: Name of the doctype to check

    Returns:
        Field name ('company' or 'custom_company') if found, None otherwise
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    try:
        # Check cache first for field name
        cache_key_name = CACHE_KEY_COMPANY_FIELD_NAME.format(doctype=doctype)
        cached_field_name = frappe.cache().get(cache_key_name)
        if cached_field_name is not None:
            # Return cached field name (could be a string or False/None)
            return cached_field_name if cached_field_name else None

        # Check if get_meta is available
        if not hasattr(frappe, "get_meta"):
            return None

        meta = frappe.get_meta(doctype)

        # Check if doctype has company field (either 'company' or 'custom_company')
        # Prefer 'company' over 'custom_company' if both exist
        found_field = None
        for field in meta.fields:
            if (
                field.fieldname in [COMPANY_FIELD_NAME, CUSTOM_COMPANY_FIELD_NAME]
                and field.fieldtype == COMPANY_FIELD_TYPE
            ):
                if field.options == COMPANY_FIELD_OPTIONS:
                    # Prefer standard 'company' field over 'custom_company'
                    if field.fieldname == COMPANY_FIELD_NAME:
                        found_field = field.fieldname
                        break
                    elif not found_field:
                        found_field = field.fieldname

        # Cache the result (store field name or None)
        frappe.cache().set(cache_key_name, found_field, expires_in_sec=CACHE_TTL)

        # Also cache boolean for has_company_field compatibility
        cache_key_bool = CACHE_KEY_COMPANY_FIELD.format(doctype=doctype)
        frappe.cache().set(cache_key_bool, bool(found_field), expires_in_sec=CACHE_TTL)

        return found_field

    except Exception as e:
        logger.warning(
            f"Error getting company field name for {doctype}: {str(e)}", exc_info=True
        )
        # Don't raise errors during permission queries
        return None


@frappe.whitelist()
def set_selected_company(company: str) -> Dict[str, str]:
    """
    Set user's selected company in session

    Args:
        company: Name of the company to set

    Returns:
        Dict with status and company name or error message
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    try:
        if company:
            # Validate company exists and user has access
            if frappe.db.exists("Company", company):
                frappe.session["selected_company"] = company

                # Clear user company cache
                user = frappe.session.user
                cache_key = CACHE_KEY_USER_COMPANY.format(user=user)
                frappe.cache().delete(cache_key)

                frappe.db.commit()
                logger.info(f"User {user} selected company: {company}")
                return {"status": "success", "company": company}

        logger.warning(f"Invalid company provided: {company}")
        return {"status": "error", "message": "Invalid company"}

    except Exception as e:
        logger = frappe.logger("company_global_filter", allow_site=True)
        logger.error(f"Error setting company: {str(e)}", exc_info=True)
        return {"status": "error", "message": "Error setting company"}


@frappe.whitelist()
def get_selected_company() -> Dict[str, Optional[str]]:
    """
    Get user's currently selected company information

    Returns:
        Dict with selected_company, default_company, and current_company
    """
    try:
        return {
            "selected_company": (
                frappe.session.get("selected_company") if frappe.session else None
            ),
            "default_company": (
                frappe.defaults.get_user_default("Company")
                if hasattr(frappe, "defaults")
                else None
            ),
            "current_company": get_user_company(),
        }
    except Exception as e:
        logger = frappe.logger("company_global_filter", allow_site=True)
        logger.warning(f"Error getting selected company: {str(e)}", exc_info=True)
        return {
            "selected_company": None,
            "default_company": None,
            "current_company": None,
        }


@frappe.whitelist()
def clear_selected_company() -> Dict[str, str]:
    """
    Clear user's selected company from session

    Returns:
        Dict with status and message
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    try:
        if frappe.session and "selected_company" in frappe.session:
            user = frappe.session.user
            del frappe.session["selected_company"]

            # Clear user company cache
            cache_key = CACHE_KEY_USER_COMPANY.format(user=user)
            frappe.cache().delete(cache_key)

            frappe.db.commit()
            logger.info(f"User {user} cleared company selection")
        return {"status": "success", "message": "Company filter cleared"}
    except Exception as e:
        logger.error(f"Error clearing company filter: {str(e)}", exc_info=True)
        return {"status": "error", "message": "Error clearing company filter"}
