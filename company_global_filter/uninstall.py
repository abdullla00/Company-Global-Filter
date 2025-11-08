# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Company Global Filter Uninstallation Module
Handles cleanup when the app is uninstalled
"""

from __future__ import unicode_literals

from typing import Dict

import frappe
from company_global_filter.constants import (
    CACHE_KEY_COMPANY_FIELD,
    CACHE_KEY_COMPANY_FIELD_NAME,
    CACHE_KEY_FIRST_SECTION_FIELD,
    CUSTOM_COMPANY_FIELD_NAME,
    LOG_CATEGORY_ERROR,
    LOG_CATEGORY_UNINSTALL,
)
from company_global_filter.install import get_all_doctypes_with_company_fields


def before_uninstall() -> Dict[str, int]:
    """
    Cleanup function called before uninstalling the app
    Removes all custom_company fields created by this app
    
    Returns:
        Dict with 'deleted' and 'errors' counts
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    try:
        logger.info("Company Global Filter: Starting uninstall cleanup")

        # Get list of all doctypes that have custom_company fields
        doctypes = get_all_doctypes_with_company_fields()

        deleted_count = 0
        error_count = 0
        skipped_count = 0

        for doctype in doctypes:
            field_name = f"{doctype}-{CUSTOM_COMPANY_FIELD_NAME}"

            try:
                # Check if custom field exists
                if frappe.db.exists("Custom Field", field_name):
                    # Delete the custom field
                    frappe.delete_doc("Custom Field", field_name, force=True)
                    deleted_count += 1
                    logger.info(f"Deleted custom_company field from {doctype}")

                    # Clear cache for the doctype
                    frappe.clear_cache(doctype=doctype)
                    
                    # Clear related cache keys
                    frappe.cache().delete(CACHE_KEY_COMPANY_FIELD.format(doctype=doctype))
                    frappe.cache().delete(CACHE_KEY_COMPANY_FIELD_NAME.format(doctype=doctype))
                    frappe.cache().delete(CACHE_KEY_FIRST_SECTION_FIELD.format(doctype=doctype))
                else:
                    skipped_count += 1
                    logger.debug(f"Custom field {field_name} does not exist, skipping")

            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error deleting custom_company field from {doctype}: {str(e)}", exc_info=True
                )
                frappe.log_error(
                    f"Error deleting custom_company field from {doctype}: {str(e)}",
                    LOG_CATEGORY_ERROR,
                )
                # Continue with other fields even if one fails

        frappe.db.commit()

        stats = {
            "deleted": deleted_count,
            "errors": error_count,
            "skipped": skipped_count,
        }
        
        logger.info(
            f"Company Global Filter: Uninstall cleanup completed. Stats: {stats}"
        )
        frappe.log_error(
            f"Company Global Filter: Uninstall cleanup completed. Deleted: {deleted_count}, Errors: {error_count}, Skipped: {skipped_count}",
            LOG_CATEGORY_UNINSTALL,
        )
        
        return stats

    except Exception as e:
        logger = frappe.logger("company_global_filter", allow_site=True)
        logger.error(
            f"Company Global Filter: Uninstall cleanup error - {str(e)}", exc_info=True
        )
        frappe.log_error(
            f"Company Global Filter: Uninstall cleanup error - {str(e)}",
            LOG_CATEGORY_ERROR,
        )
        # Don't raise - allow uninstall to continue even if cleanup fails
        return {"deleted": 0, "errors": 1, "skipped": 0}

