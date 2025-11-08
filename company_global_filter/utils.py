# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Utility functions for Company Global Filter App
"""

from __future__ import unicode_literals

from typing import List, Optional

import frappe
from company_global_filter.constants import (
    CACHE_KEY_COMPANY_FIELD,
    CACHE_KEY_COMPANY_FIELD_NAME,
    CACHE_KEY_FIRST_SECTION_FIELD,
    CACHE_KEY_USER_COMPANY,
)


def clear_company_filter_cache(doctype: Optional[str] = None, user: Optional[str] = None) -> None:
    """
    Clear cache related to company filtering
    
    Args:
        doctype: Optional doctype name to clear cache for specific doctype
        user: Optional username to clear cache for specific user
    """
    if doctype:
        # Clear doctype-specific cache
        frappe.cache().delete(CACHE_KEY_COMPANY_FIELD.format(doctype=doctype))
        frappe.cache().delete(CACHE_KEY_COMPANY_FIELD_NAME.format(doctype=doctype))
        frappe.cache().delete(CACHE_KEY_FIRST_SECTION_FIELD.format(doctype=doctype))
        frappe.clear_cache(doctype=doctype)
    elif user:
        # Clear user-specific cache
        frappe.cache().delete(CACHE_KEY_USER_COMPANY.format(user=user))
        # Clear excluded companies cache for this user
        for key in frappe.cache().keys(f"cgf:excluded_companies:{user}:*"):
            frappe.cache().delete(key)
    else:
        # Clear all company filter cache
        # Clear excluded companies cache
        for key in frappe.cache().keys("cgf:excluded_companies:*"):
            frappe.cache().delete(key)
        frappe.clear_cache()


def get_filtered_doctypes() -> List[str]:
    """
    Get list of all doctypes that have company filtering enabled
    
    Returns:
        List of doctype names that have company or custom_company fields
    """
    from company_global_filter.install import get_all_doctypes_with_company_fields
    from company_global_filter.hook_functions.global_company_filter import get_company_field_name
    
    doctypes = get_all_doctypes_with_company_fields()
    filtered_doctypes = []
    
    for doctype in doctypes:
        if get_company_field_name(doctype):
            filtered_doctypes.append(doctype)
    
    return filtered_doctypes

