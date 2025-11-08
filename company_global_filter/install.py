# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Company Global Filter Installation Module
Handles post-installation setup to add custom_company fields to doctypes
"""

from __future__ import unicode_literals

from typing import Any, Dict, List, Optional

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from company_global_filter.constants import (
    CACHE_KEY_COMPANY_FIELD,
    CACHE_KEY_FIRST_SECTION_FIELD,
    CACHE_TTL,
    COMPANY_FIELD_DESCRIPTION,
    COMPANY_FIELD_LABEL,
    COMPANY_FIELD_NAME,
    COMPANY_FIELD_OPTIONS,
    COMPANY_FIELD_TYPE,
    CUSTOM_COMPANY_FIELD_NAME,
    FIELD_PROPERTIES,
    LAYOUT_FIELD_TYPES,
    LOG_CATEGORY_ERROR,
    LOG_CATEGORY_INSTALL,
    SHARED_MASTER_DOCTYPES,
    SYSTEM_DOCTYPES,
)
from company_global_filter.doctype.company_global_filter_settings.company_global_filter_settings import (
    get_settings,
)


def after_install() -> None:
    """
    Main after_install function
    Called automatically after app installation
    
    Raises:
        Exception: If installation fails
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    try:
        logger.info("Company Global Filter: Starting installation")

        # Get settings to check if auto_create_fields is enabled
        settings = get_settings()
        
        if settings.auto_create_fields:
            # Create custom company fields for all doctypes
            create_company_filter_fields()
            
            # Create database indexes for performance
            create_company_field_indexes()
        else:
            logger.info("Auto create fields is disabled in settings, skipping field creation")

        frappe.db.commit()
        logger.info("Company Global Filter: Installation completed successfully")

    except Exception as e:
        logger.error(f"Company Global Filter: Installation error - {str(e)}", exc_info=True)
        frappe.log_error(
            f"Company Global Filter: Installation error - {str(e)}", LOG_CATEGORY_ERROR
        )
        raise


def create_company_filter_fields() -> Dict[str, int]:
    """
    Create or update custom_company fields for all doctypes that need company filtering
    Updates existing fields if they have incorrect placement
    
    Returns:
        Dict with 'created', 'updated', 'skipped', 'errors' counts
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    custom_fields = get_custom_fields()

    # Fields to create or update
    fields_to_process = {}
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    for doctype, fields in custom_fields.items():
        try:
            # Check if doctype exists
            if not doctype_exists(doctype):
                logger.warning(f"DocType {doctype} does not exist, skipping")
                stats["skipped"] += 1
                continue

            # Get the expected field configuration
            expected_field = fields[0]  # There's only one field per doctype
            expected_insert_after = expected_field.get("insert_after")

            # Check if custom_company field already exists
            field_name = f"{doctype}-{CUSTOM_COMPANY_FIELD_NAME}"
            existing_field = None
            if frappe.db.exists("Custom Field", field_name):
                try:
                    existing_field = frappe.get_doc("Custom Field", field_name)
                except Exception as e:
                    logger.warning(f"Error loading existing field for {doctype}: {str(e)}")
                    stats["errors"] += 1
                    continue

            # If field exists, check if it needs updating
            if existing_field:
                current_insert_after = existing_field.get("insert_after")

                # Check if placement needs updating
                if current_insert_after != expected_insert_after:
                    logger.info(
                        f"{doctype}: updating placement from '{current_insert_after}' to '{expected_insert_after}'"
                    )
                    # Include in fields to update
                    fields_to_process[doctype] = fields
                    stats["updated"] += 1
                else:
                    logger.debug(
                        f"DocType {doctype}: custom_company field already exists with correct placement, skipping"
                    )
                    stats["skipped"] += 1
            else:
                # Field doesn't exist, check if standard company field exists
                if has_company_field(doctype):
                    logger.info(
                        f"DocType {doctype} already has standard company field, skipping custom_company"
                    )
                    stats["skipped"] += 1
                    continue

                # Field doesn't exist, create it
                logger.info(f"DocType {doctype}: custom_company field does not exist, will create")
                fields_to_process[doctype] = fields
                stats["created"] += 1

        except Exception as e:
            logger.error(f"Error processing doctype {doctype}: {str(e)}", exc_info=True)
            stats["errors"] += 1
            continue

    if fields_to_process:
        try:
            create_custom_fields(fields_to_process, ignore_validate=True, update=True)
            logger.info(
                f"Created/updated custom_company fields for {len(fields_to_process)} doctypes. "
                f"Stats: {stats}"
            )
        except Exception as e:
            logger.error(f"Error creating/updating custom fields: {str(e)}", exc_info=True)
            frappe.log_error(
                f"Error creating/updating custom fields: {str(e)}", LOG_CATEGORY_ERROR
            )
            raise
    else:
        logger.info(f"No custom fields to create or update. Stats: {stats}")

    return stats


def doctype_exists(doctype: str) -> bool:
    """
    Check if a doctype exists in the system
    
    Args:
        doctype: Name of the doctype to check
        
    Returns:
        True if doctype exists, False otherwise
    """
    try:
        return frappe.db.exists("DocType", doctype)
    except Exception:
        return False


def has_company_field(doctype: str) -> bool:
    """
    Check if doctype already has company or custom_company field
    Uses caching to improve performance
    
    Args:
        doctype: Name of the doctype to check
        
    Returns:
        True if doctype has company field, False otherwise
    """
    # Check cache first
    cache_key = CACHE_KEY_COMPANY_FIELD.format(doctype=doctype)
    cached_result = frappe.cache().get(cache_key)
    if cached_result is not None:
        return cached_result

    try:
        meta = frappe.get_meta(doctype)
        for field in meta.fields:
            if (
                field.fieldname in [COMPANY_FIELD_NAME, CUSTOM_COMPANY_FIELD_NAME]
                and field.fieldtype == COMPANY_FIELD_TYPE
            ):
                if field.options == COMPANY_FIELD_OPTIONS:
                    # Cache the result
                    frappe.cache().set(cache_key, True, expires_in_sec=CACHE_TTL)
                    return True
        # Cache negative result too
        frappe.cache().set(cache_key, False, expires_in_sec=CACHE_TTL)
        return False
    except Exception:
        return False


def get_first_section_last_field(doctype: str) -> Optional[str]:
    """
    Find the last field in the first section of the first tab.
    Returns the fieldname to use for insert_after, or None if not found.
    Uses caching to improve performance.

    Logic:
    1. Skip any initial Tab Breaks/Section Breaks to find the first actual section
    2. Once we encounter the first non-break field, start tracking
    3. Track the last visible, non-layout field (excluding custom_company)
    4. When we encounter the first Section Break, return the last tracked field
    5. If no Section Break is found in first tab, return the last field before Tab Break or end
    
    Args:
        doctype: Name of the doctype to analyze
        
    Returns:
        Fieldname of the last field in first section, or None if not found
        
    Raises:
        None - Returns None on any error to allow graceful degradation
    """
    # Check cache first
    cache_key = CACHE_KEY_FIRST_SECTION_FIELD.format(doctype=doctype)
    cached_result = frappe.cache().get(cache_key)
    # Only use cache if it's a valid string (not None, not empty)
    if cached_result is not None and isinstance(cached_result, str) and cached_result:
        return cached_result

    try:
        meta = frappe.get_meta(doctype)
        last_field = None
        in_first_section = False
        logger = frappe.logger("company_global_filter", allow_site=True)

        for field in meta.fields:
            # Skip custom_company field itself
            if field.fieldname == CUSTOM_COMPANY_FIELD_NAME:
                continue

            # Handle Tab/Section Breaks
            if field.fieldtype in ["Tab Break", "Section Break"]:
                if not in_first_section:
                    # Still skipping initial breaks, continue
                    continue
                elif field.fieldtype == "Section Break":
                    # Found first Section Break, return last field
                    result = last_field
                    # Cache the result (only if valid)
                    if result:
                        try:
                            frappe.cache().set(cache_key, result, expires_in_sec=CACHE_TTL)
                        except Exception:
                            # Cache failure shouldn't prevent returning the result
                            pass
                    return result
                elif field.fieldtype == "Tab Break":
                    # Left first tab, return last field
                    result = last_field
                    # Cache the result (only if valid)
                    if result:
                        try:
                            frappe.cache().set(cache_key, result, expires_in_sec=CACHE_TTL)
                        except Exception:
                            # Cache failure shouldn't prevent returning the result
                            pass
                    return result

            # Skip hidden and layout fields (but don't mark as in_first_section yet)
            if field.hidden or field.fieldtype in LAYOUT_FIELD_TYPES:
                continue

            # Mark that we've entered the first section (first visible, non-layout field)
            if not in_first_section:
                in_first_section = True

            # Track this field as the last field in first section
            last_field = field.fieldname
            logger.debug(f"{doctype}: Tracking field '{field.fieldname}' as last_field in first section")

        # Return last field found (if no Section Break encountered)
        result = last_field
        logger.debug(f"{doctype}: Returning last_field = {result} (no Section Break encountered)")
        # Cache the result (only if valid, not None)
        if result:
            try:
                frappe.cache().set(cache_key, result, expires_in_sec=CACHE_TTL)
            except Exception:
                # Cache failure shouldn't prevent returning the result
                pass
        return result

    except Exception as e:
        logger = frappe.logger("company_global_filter", allow_site=True)
        error_msg = f"Error finding first section last field for {doctype}: {str(e)}"
        logger.warning(error_msg, exc_info=True)
        frappe.log_error(error_msg, LOG_CATEGORY_INSTALL)
        # Don't cache None on error - allow retry
        return None


def get_all_doctypes_with_company_fields() -> List[str]:
    """
    Get list of all doctypes that should have custom_company fields
    Used for both installation and uninstallation
    
    Returns:
        List of doctype names that should have custom_company fields
    """
    # Combine system and shared master doctypes from constants
    return SYSTEM_DOCTYPES + SHARED_MASTER_DOCTYPES


def get_custom_fields() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get dictionary of custom_company field definitions for all doctypes
    Fields will be placed in the first tab, first section, after the last field
    
    Returns:
        Dictionary mapping doctype names to lists of field definitions
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    # Get list of all doctypes
    all_doctypes = get_all_doctypes_with_company_fields()

    # Create custom fields dictionary with dynamic insert_after
    custom_fields = {}
    for doctype in all_doctypes:
        # Find the last field in the first section
        insert_after_field = get_first_section_last_field(doctype)

        # Get settings to determine field placement
        settings = get_settings()
        placement = settings.get("field_placement", "First Section")
        
        # If no field found or placement is "Append to Form", fall back to "append"
        if placement == "Append to Form" or not insert_after_field:
            insert_after = "append"
        else:
            insert_after = insert_after_field

        # Standard field configuration for custom_company
        company_field = {
            "fieldname": CUSTOM_COMPANY_FIELD_NAME,
            "fieldtype": COMPANY_FIELD_TYPE,
            "options": COMPANY_FIELD_OPTIONS,
            "label": COMPANY_FIELD_LABEL,
            "insert_after": insert_after,
            "description": COMPANY_FIELD_DESCRIPTION,
            **FIELD_PROPERTIES,
        }

        custom_fields[doctype] = [company_field]

        if insert_after_field:
            logger.debug(
                f"DocType {doctype}: custom_company will be inserted after '{insert_after_field}'"
            )
        else:
            logger.debug(
                f"DocType {doctype}: custom_company will be appended (no field found in first section)"
            )

    return custom_fields


def create_company_field_indexes() -> Dict[str, int]:
    """
    Create database indexes on custom_company fields for better query performance
    
    Returns:
        Dict with 'created', 'skipped', 'errors' counts
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    stats = {"created": 0, "skipped": 0, "errors": 0}
    
    doctypes = get_all_doctypes_with_company_fields()
    
    for doctype in doctypes:
        try:
            # Check if doctype exists
            if not doctype_exists(doctype):
                stats["skipped"] += 1
                continue
            
            # Check if custom_company field exists
            field_name = f"{doctype}-{CUSTOM_COMPANY_FIELD_NAME}"
            if not frappe.db.exists("Custom Field", field_name):
                # Check if standard company field exists
                if not has_company_field(doctype):
                    stats["skipped"] += 1
                    continue
            
            # Determine which field to index
            meta = frappe.get_meta(doctype)
            
            # Skip Single DocTypes - they don't have database tables
            if meta.is_single:
                stats["skipped"] += 1
                continue
            
            company_field = None
            for field in meta.fields:
                if field.fieldname in [COMPANY_FIELD_NAME, CUSTOM_COMPANY_FIELD_NAME]:
                    if field.fieldtype == COMPANY_FIELD_TYPE and field.options == COMPANY_FIELD_OPTIONS:
                        company_field = field.fieldname
                        break
            
            if not company_field:
                stats["skipped"] += 1
                continue
            
            # Check if index already exists
            table_name = f"tab{doctype}"
            index_name = f"idx_{company_field}"
            
            # Get existing indexes - SHOW INDEX doesn't support WHERE, so fetch all and filter
            try:
                all_indexes = frappe.db.sql(
                    f"SHOW INDEX FROM `{table_name}`",
                    as_dict=True,
                )
                # Filter for our index name
                existing_indexes = [idx for idx in all_indexes if idx.get("Key_name") == index_name]
            except Exception as e:
                # Table might not exist or other error (e.g., Single DocType)
                logger.debug(f"Could not check indexes for {table_name}: {str(e)}")
                existing_indexes = []
            
            if existing_indexes:
                logger.debug(f"Index {index_name} already exists on {table_name}")
                stats["skipped"] += 1
                continue
            
            # Create index
            try:
                frappe.db.sql(
                    f"CREATE INDEX `{index_name}` ON `{table_name}` (`{company_field}`)"
                )
                logger.info(f"Created index {index_name} on {table_name}.{company_field}")
                stats["created"] += 1
            except Exception as e:
                # Index might already exist or table might not exist yet
                logger.warning(f"Could not create index {index_name} on {table_name}: {str(e)}")
                stats["errors"] += 1
                continue
                
        except Exception as e:
            logger.error(f"Error creating index for {doctype}: {str(e)}", exc_info=True)
            stats["errors"] += 1
            continue
    
    logger.info(f"Index creation completed. Stats: {stats}")
    return stats
