# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Company Global Filter Uninstallation Module
Handles cleanup when the app is uninstalled
"""

from __future__ import unicode_literals

from typing import Dict, List

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


def _get_child_table_doctypes() -> List[str]:
    """
    Get list of all child table DocTypes that should be deleted during uninstall.
    
    Note: These DocTypes belong to the "Company Global Filter" module and should
    be automatically deleted by Frappe during uninstall. This list is used for
    verification and fallback cleanup in after_uninstall.
    
    Returns:
        List of child table DocType names
    """
    return [
        "CGF Excluded Company",
        "CGF Excluded Company User",
        "CGF Excluded Company Role",
        "CGF Per DocType Excluded Company",
    ]


def _verify_cleanup() -> Dict[str, bool]:
    """
    Verify that cleanup was successful by checking if expected items still exist.
    
    Returns:
        Dict with verification status for each item type:
        - custom_fields_removed: True if all custom company fields are removed
        - settings_fields_removed: True if Settings DocType fields are removed
        - child_doctypes_removed: True if all child table DocTypes are removed
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    result = {
        "custom_fields_removed": True,
        "settings_fields_removed": True,
        "child_doctypes_removed": True,
    }
    
    # Check custom company fields
    doctypes = get_all_doctypes_with_company_fields()
    for doctype in doctypes:
        field_name = f"{doctype}-{CUSTOM_COMPANY_FIELD_NAME}"
        if frappe.db.exists("Custom Field", field_name):
            result["custom_fields_removed"] = False
            logger.warning(f"Custom field {field_name} still exists after cleanup")
    
    # Check Settings DocType fields
    if frappe.db.exists("DocType", "Company Global Filter Settings"):
        meta = frappe.get_meta("Company Global Filter Settings")
        if meta.get_field("excluded_companies") or meta.get_field("per_doctype_excluded_companies"):
            result["settings_fields_removed"] = False
            logger.warning("Settings DocType fields still exist after cleanup")
    
    # Check child table DocTypes
    child_table_doctypes = _get_child_table_doctypes()
    for doctype_name in child_table_doctypes:
        if frappe.db.exists("DocType", doctype_name):
            result["child_doctypes_removed"] = False
            logger.warning(f"Child table DocType {doctype_name} still exists after cleanup")
    
    return result


def before_uninstall() -> Dict[str, int]:
    """
    Cleanup function called before uninstalling the app.
    
    Removes all custom_company fields created by this app and Settings DocType fields.
    Note: Child table DocTypes are automatically deleted by Frappe during uninstall
    since they belong to the "Company Global Filter" module. We rely on Frappe's
    automatic deletion for DocTypes to avoid conflicts.
    
    Returns:
        Dict with cleanup statistics:
        - deleted: Number of items successfully deleted
        - skipped: Number of items that didn't exist (not an error)
        - errors: Number of items that failed to delete
        - verified: Number of items verified as deleted
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    try:
        logger.info("Company Global Filter: Starting uninstall cleanup (before_uninstall)")

        # Get list of all doctypes that have custom_company fields
        doctypes = get_all_doctypes_with_company_fields()
        logger.info(f"Processing {len(doctypes)} doctypes for custom company field removal")

        deleted_count = 0
        error_count = 0
        skipped_count = 0
        verified_count = 0

        # Delete custom company fields
        for doctype in doctypes:
            field_name = f"{doctype}-{CUSTOM_COMPANY_FIELD_NAME}"

            try:
                # Check if custom field exists
                if frappe.db.exists("Custom Field", field_name):
                    # Delete the custom field
                    frappe.delete_doc("Custom Field", field_name, force=True)
                    # Explicit commit after each deletion to ensure persistence
                    frappe.db.commit()
                    deleted_count += 1
                    logger.info(f"Deleted custom_company field from {doctype}")

                    # Verify deletion
                    if frappe.db.exists("Custom Field", field_name):
                        logger.warning(f"Custom field {field_name} still exists after deletion attempt")
                        error_count += 1
                    else:
                        verified_count += 1
                        # Clear cache for the doctype
                        frappe.clear_cache(doctype=doctype)
                        
                        # Clear related cache keys
                        frappe.cache().delete(CACHE_KEY_COMPANY_FIELD.format(doctype=doctype))
                        frappe.cache().delete(CACHE_KEY_COMPANY_FIELD_NAME.format(doctype=doctype))
                        frappe.cache().delete(CACHE_KEY_FIRST_SECTION_FIELD.format(doctype=doctype))
                else:
                    skipped_count += 1
                    logger.debug(f"Custom field {field_name} does not exist, skipping")

            except frappe.DoesNotExistError:
                skipped_count += 1
                logger.debug(f"Custom field {field_name} does not exist (DoesNotExistError), skipping")
            except frappe.ValidationError as e:
                error_count += 1
                logger.error(
                    f"Validation error deleting custom_company field from {doctype}: {str(e)}", exc_info=True
                )
                frappe.log_error(
                    f"Validation error deleting custom_company field from {doctype}: {str(e)}",
                    LOG_CATEGORY_ERROR,
                )
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

        # Note: Child table DocTypes are NOT explicitly deleted here.
        # Frappe automatically deletes all DocTypes in the app's modules during uninstall.
        # The child table DocTypes belong to "Company Global Filter" module and will be
        # automatically deleted by Frappe's _delete_modules() function.
        logger.info("Relying on Frappe's automatic deletion for child table DocTypes in module")
        
        # Remove excluded companies fields from Settings DocType if it exists
        settings_fields_removed = False
        try:
            if frappe.db.exists("DocType", "Company Global Filter Settings"):
                settings_dt = frappe.get_doc("DocType", "Company Global Filter Settings")
                fields_to_remove = ["excluded_companies_section", "excluded_companies", "per_doctype_excluded_companies"]
                fields_removed_count = 0
                
                for fieldname in fields_to_remove:
                    # Remove field from fields list
                    fields_to_delete = [f for f in settings_dt.fields if f.fieldname == fieldname]
                    for field in fields_to_delete:
                        settings_dt.fields.remove(field)
                        fields_removed_count += 1
                        logger.info(f"Removed field {fieldname} from Settings DocType")
                
                if fields_removed_count > 0:
                    # Update field_order
                    if hasattr(settings_dt, 'field_order') and settings_dt.field_order:
                        import json
                        field_order = json.loads(settings_dt.field_order) if isinstance(settings_dt.field_order, str) else settings_dt.field_order
                        field_order = [f for f in field_order if f not in fields_to_remove]
                        settings_dt.field_order = json.dumps(field_order) if isinstance(settings_dt.field_order, str) else field_order
                    
                    settings_dt.save(ignore_permissions=True)
                    # Explicit commit after Settings DocType modification
                    frappe.db.commit()
                    logger.info(f"Updated Settings DocType to remove {fields_removed_count} excluded companies fields")
                    
                    # Verify fields are removed
                    meta = frappe.get_meta("Company Global Filter Settings")
                    if not meta.get_field("excluded_companies") and not meta.get_field("per_doctype_excluded_companies"):
                        settings_fields_removed = True
                        verified_count += fields_removed_count
                        logger.info("Verified: Settings DocType fields successfully removed")
                    else:
                        logger.warning("Settings DocType fields may not have been fully removed")
                else:
                    logger.debug("No excluded companies fields found in Settings DocType to remove")
            else:
                logger.debug("Settings DocType does not exist, skipping field removal")
        except frappe.DoesNotExistError:
            logger.debug("Settings DocType does not exist (DoesNotExistError), skipping field removal")
        except Exception as e:
            logger.error(
                f"Error removing excluded companies fields from Settings DocType: {str(e)}", exc_info=True
            )
            frappe.log_error(
                f"Error removing excluded companies fields from Settings DocType: {str(e)}",
                LOG_CATEGORY_ERROR,
            )

        stats = {
            "deleted": deleted_count,
            "errors": error_count,
            "skipped": skipped_count,
            "verified": verified_count,
        }
        
        logger.info(
            f"Company Global Filter: before_uninstall cleanup completed. Stats: {stats}"
        )
        frappe.log_error(
            f"Company Global Filter: before_uninstall cleanup completed. Deleted: {deleted_count}, Errors: {error_count}, Skipped: {skipped_count}, Verified: {verified_count}",
            LOG_CATEGORY_UNINSTALL,
        )
        
        return stats

    except Exception as e:
        logger = frappe.logger("company_global_filter", allow_site=True)
        logger.error(
            f"Company Global Filter: before_uninstall cleanup error - {str(e)}", exc_info=True
        )
        frappe.log_error(
            f"Company Global Filter: before_uninstall cleanup error - {str(e)}",
            LOG_CATEGORY_ERROR,
        )
        # Don't raise - allow uninstall to continue even if cleanup fails
        return {"deleted": 0, "errors": 1, "skipped": 0, "verified": 0}


def after_uninstall() -> Dict[str, int]:
    """
    Fallback cleanup function called after uninstalling the app.
    
    This serves as a safety net to catch any items that weren't deleted in
    before_uninstall or by Frappe's automatic deletion process. Checks for:
    - Remaining child table DocTypes (should have been deleted by Frappe)
    - Remaining custom company fields (should have been deleted in before_uninstall)
    - Remaining Settings DocType fields (should have been removed in before_uninstall)
    
    Returns:
        Dict with cleanup statistics:
        - deleted: Number of items successfully deleted
        - skipped: Number of items that didn't exist (not an error)
        - errors: Number of items that failed to delete
        - verified: Number of items verified as deleted
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    try:
        logger.info("Company Global Filter: Starting fallback cleanup (after_uninstall)")

        deleted_count = 0
        error_count = 0
        skipped_count = 0
        verified_count = 0

        # Check and delete any remaining child table DocTypes
        # These should have been deleted by Frappe automatically, but we check as fallback
        child_table_doctypes = _get_child_table_doctypes()
        logger.info(f"Checking {len(child_table_doctypes)} child table DocTypes for cleanup")
        
        for doctype_name in child_table_doctypes:
            try:
                if frappe.db.exists("DocType", doctype_name):
                    logger.warning(f"Child table DocType {doctype_name} still exists, attempting deletion")
                    frappe.delete_doc("DocType", doctype_name, force=True, ignore_permissions=True)
                    frappe.db.commit()
                    deleted_count += 1
                    logger.info(f"Deleted child table DocType: {doctype_name}")
                    
                    # Verify deletion
                    if frappe.db.exists("DocType", doctype_name):
                        logger.warning(f"Child table DocType {doctype_name} still exists after deletion attempt")
                        error_count += 1
                    else:
                        verified_count += 1
                else:
                    skipped_count += 1
                    logger.debug(f"Child table DocType {doctype_name} does not exist, skipping")
            except frappe.DoesNotExistError:
                skipped_count += 1
                logger.debug(f"Child table DocType {doctype_name} does not exist (DoesNotExistError), skipping")
            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error deleting child table DocType {doctype_name}: {str(e)}", exc_info=True
                )
                frappe.log_error(
                    f"Error deleting child table DocType {doctype_name}: {str(e)}",
                    LOG_CATEGORY_ERROR,
                )

        # Check and delete any remaining custom company fields
        doctypes = get_all_doctypes_with_company_fields()
        logger.info(f"Checking {len(doctypes)} doctypes for remaining custom company fields")
        
        for doctype in doctypes:
            field_name = f"{doctype}-{CUSTOM_COMPANY_FIELD_NAME}"

            try:
                if frappe.db.exists("Custom Field", field_name):
                    logger.warning(f"Custom field {field_name} still exists, attempting deletion")
                    frappe.delete_doc("Custom Field", field_name, force=True)
                    frappe.db.commit()
                    deleted_count += 1
                    logger.info(f"Deleted custom_company field from {doctype}")
                    
                    # Verify deletion
                    if frappe.db.exists("Custom Field", field_name):
                        logger.warning(f"Custom field {field_name} still exists after deletion attempt")
                        error_count += 1
                    else:
                        verified_count += 1
                        # Clear cache
                        frappe.clear_cache(doctype=doctype)
                        frappe.cache().delete(CACHE_KEY_COMPANY_FIELD.format(doctype=doctype))
                        frappe.cache().delete(CACHE_KEY_COMPANY_FIELD_NAME.format(doctype=doctype))
                        frappe.cache().delete(CACHE_KEY_FIRST_SECTION_FIELD.format(doctype=doctype))
                else:
                    skipped_count += 1
            except frappe.DoesNotExistError:
                skipped_count += 1
            except Exception as e:
                error_count += 1
                logger.error(
                    f"Error deleting custom_company field from {doctype}: {str(e)}", exc_info=True
                )

        # Check and remove any remaining Settings DocType fields
        try:
            if frappe.db.exists("DocType", "Company Global Filter Settings"):
                meta = frappe.get_meta("Company Global Filter Settings")
                excluded_companies_field = meta.get_field("excluded_companies")
                per_doctype_field = meta.get_field("per_doctype_excluded_companies")
                
                if excluded_companies_field or per_doctype_field:
                    logger.warning("Settings DocType fields still exist, attempting removal")
                    settings_dt = frappe.get_doc("DocType", "Company Global Filter Settings")
                    fields_to_remove = ["excluded_companies_section", "excluded_companies", "per_doctype_excluded_companies"]
                    fields_removed_count = 0
                    
                    for fieldname in fields_to_remove:
                        fields_to_delete = [f for f in settings_dt.fields if f.fieldname == fieldname]
                        for field in fields_to_delete:
                            settings_dt.fields.remove(field)
                            fields_removed_count += 1
                            logger.info(f"Removed field {fieldname} from Settings DocType")
                    
                    if fields_removed_count > 0:
                        # Update field_order
                        if hasattr(settings_dt, 'field_order') and settings_dt.field_order:
                            import json
                            field_order = json.loads(settings_dt.field_order) if isinstance(settings_dt.field_order, str) else settings_dt.field_order
                            field_order = [f for f in field_order if f not in fields_to_remove]
                            settings_dt.field_order = json.dumps(field_order) if isinstance(settings_dt.field_order, str) else field_order
                        
                        settings_dt.save(ignore_permissions=True)
                        frappe.db.commit()
                        deleted_count += fields_removed_count
                        logger.info(f"Removed {fields_removed_count} fields from Settings DocType")
                        
                        # Verify removal
                        meta = frappe.get_meta("Company Global Filter Settings")
                        if not meta.get_field("excluded_companies") and not meta.get_field("per_doctype_excluded_companies"):
                            verified_count += fields_removed_count
                            logger.info("Verified: Settings DocType fields successfully removed")
                        else:
                            logger.warning("Settings DocType fields may not have been fully removed")
                else:
                    skipped_count += 1
                    logger.debug("Settings DocType fields already removed")
            else:
                skipped_count += 1
                logger.debug("Settings DocType does not exist, skipping")
        except frappe.DoesNotExistError:
            skipped_count += 1
            logger.debug("Settings DocType does not exist (DoesNotExistError), skipping")
        except Exception as e:
            error_count += 1
            logger.error(
                f"Error removing Settings DocType fields: {str(e)}", exc_info=True
            )

        # Perform final verification
        verification = _verify_cleanup()
        if not all(verification.values()):
            logger.warning(f"Cleanup verification failed: {verification}")
        else:
            logger.info("Cleanup verification passed: All items successfully removed")

        stats = {
            "deleted": deleted_count,
            "errors": error_count,
            "skipped": skipped_count,
            "verified": verified_count,
        }
        
        logger.info(
            f"Company Global Filter: after_uninstall cleanup completed. Stats: {stats}"
        )
        frappe.log_error(
            f"Company Global Filter: after_uninstall cleanup completed. Deleted: {deleted_count}, Errors: {error_count}, Skipped: {skipped_count}, Verified: {verified_count}",
            LOG_CATEGORY_UNINSTALL,
        )
        
        return stats

    except Exception as e:
        logger = frappe.logger("company_global_filter", allow_site=True)
        logger.error(
            f"Company Global Filter: after_uninstall cleanup error - {str(e)}", exc_info=True
        )
        frappe.log_error(
            f"Company Global Filter: after_uninstall cleanup error - {str(e)}",
            LOG_CATEGORY_ERROR,
        )
        # Don't raise - allow uninstall to continue even if cleanup fails
        return {"deleted": 0, "errors": 1, "skipped": 0, "verified": 0}

