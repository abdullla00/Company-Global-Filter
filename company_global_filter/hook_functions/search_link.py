from __future__ import unicode_literals

from typing import Any, Dict, Optional

import frappe
from frappe import _
from frappe.desk.search import search_link as frappe_search_link

from company_global_filter.constants import (
    COMPANY_FIELD_NAME,
    CUSTOM_COMPANY_FIELD_NAME,
    IGNORE_DOCTYPES,
    LOG_CATEGORY_DEBUG,
)
from company_global_filter.doctype.company_global_filter_settings.company_global_filter_settings import (
    get_excluded_companies_for_user,
)
from company_global_filter.hook_functions.global_company_filter import (
    get_company_field_name,
    get_user_company,
)


@frappe.whitelist()
def search_link(
	doctype: Optional[str] = None,
	txt: Optional[str] = None,
	query: Optional[str] = None,
	filters: Optional[Dict[str, Any]] = None,
	page_length: int = 20,
	searchfield: Optional[str] = None,
	reference_doctype: Optional[str] = None,
	ignore_user_permissions: bool = False,
) -> list:
	"""
	Extended search_link method that applies company filtering
	
	Args:
		doctype: Name of the doctype to search
		txt: Search text
		query: Custom query string
		filters: Additional filters to apply
		page_length: Number of results to return
		searchfield: Field to search in
		reference_doctype: Reference doctype for link fields
		ignore_user_permissions: Whether to ignore user permissions
		
	Returns:
		List of search results
	"""
	logger = frappe.logger("company_global_filter", allow_site=True)
	try:
		# Use passed parameters if available, otherwise get from form_dict
		doctype = doctype or frappe.form_dict.get("doctype")
		txt = txt or frappe.form_dict.get("txt")
		query = query or frappe.form_dict.get("query")
		filters = filters or frappe.parse_json(frappe.form_dict.get("filters") or "{}")
		page_length = page_length or frappe.form_dict.get("page_length", 20)
		searchfield = searchfield or frappe.form_dict.get("searchfield")
		reference_doctype = reference_doctype or frappe.form_dict.get("reference_doctype")
		ignore_user_permissions = ignore_user_permissions or frappe.form_dict.get("ignore_user_permissions")
		ignore_user_permissions = str(ignore_user_permissions).lower() in ["1", "true", "yes"]

		if not doctype:
			return frappe_search_link(
				doctype=doctype,
				txt=txt,
				query=query,
				filters=filters,
				page_length=page_length,
				searchfield=searchfield,
				reference_doctype=reference_doctype,
				ignore_user_permissions=ignore_user_permissions,
			)

		# Get user's company
		user_company = get_user_company()
		if not user_company:
			logger.debug(f"No company found for user, skipping filter for {doctype}")
			return frappe_search_link(
				doctype=doctype,
				txt=txt,
				query=query,
				filters=filters,
				page_length=page_length,
				searchfield=searchfield,
				reference_doctype=reference_doctype,
				ignore_user_permissions=ignore_user_permissions,
			)

		# Skip company filtering for ignored doctypes
		if doctype in IGNORE_DOCTYPES:
			return frappe_search_link(
				doctype=doctype or "",
				txt=txt or "",
				query=query or "",
				filters=filters or {},
				page_length=page_length or 20,
				searchfield=searchfield or "name",
				reference_doctype=reference_doctype or "",
				ignore_user_permissions=bool(ignore_user_permissions),
			)

		# Check if doctype has company field using cached function
		company_field_name = get_company_field_name(doctype)

		# If no company field exists, return original search
		if not company_field_name:
			return frappe_search_link(
				doctype=doctype,
				txt=txt,
				query=query,
				filters=filters,
				page_length=page_length,
				searchfield=searchfield,
				reference_doctype=reference_doctype,
				ignore_user_permissions=ignore_user_permissions,
			)

		# Initialize filters if not exists
		if not filters:
			filters = {}

		# Get excluded companies for this user and doctype
		user = frappe.session.user if hasattr(frappe, 'session') and frappe.session else None
		excluded_companies = get_excluded_companies_for_user(user, doctype) if user else []

		# Add company filter - include user's company and excluded companies
		if excluded_companies:
			# Use "in" operator to include both user's company and excluded companies
			companies_list = [user_company] + excluded_companies
			filters[company_field_name] = ["in", companies_list]
			logger.debug(f"Applied company filter with excluded companies to search_link for {doctype}: {filters}")
		else:
			# Standard filter with just user's company
			filters[company_field_name] = user_company
			logger.debug(f"Applied company filter to search_link for {doctype}: {filters}")

		# Update form_dict filters for consistency
		frappe.form_dict["filters"] = frappe.as_json(filters)
		return frappe_search_link(
			doctype=doctype,
			txt=txt,
			query=query,
			filters=filters,
			page_length=page_length,
			searchfield=searchfield,
			reference_doctype=reference_doctype,
			ignore_user_permissions=ignore_user_permissions,
		)
	except Exception as e:
		logger = frappe.logger("company_global_filter", allow_site=True)
		logger.warning(f"Error in search_link for {doctype}: {str(e)}", exc_info=True)
		frappe.log_error(f"Error in search_link: {str(e)}", "Search Link Error")
		# Fallback to original search on error
		return frappe_search_link(
			doctype=doctype,
			txt=txt,
			query=query,
			filters=filters,
			page_length=page_length,
			searchfield=searchfield,
			reference_doctype=reference_doctype,
			ignore_user_permissions=ignore_user_permissions,
		)
