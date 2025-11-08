# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Constants for Company Global Filter App
Centralized configuration values and magic strings
"""

from __future__ import unicode_literals

# Field names
COMPANY_FIELD_NAME = "company"
CUSTOM_COMPANY_FIELD_NAME = "custom_company"

# Field configuration
COMPANY_FIELD_TYPE = "Link"
COMPANY_FIELD_OPTIONS = "Company"
COMPANY_FIELD_LABEL = "Company"
COMPANY_FIELD_DESCRIPTION = "Company filter for Company Global Filter app"

# System doctypes that should never be filtered
SYSTEM_DOCTYPES = [
    # Core system doctypes that could break boot process
    "User",
    "Role",
    "DocType",
    "DocField",
    "DocPerm",
    "Print Format",
    "Page",
    "Report",
    "Module Def",
    "Desktop Icon",
    "Workspace",
    "Dashboard",
    "Number Card",
    "Dashboard Chart",
    "Session Default",
    "System Settings",
    "Error Log",
    "Activity Log",
    "Email Queue",
    "Communication",
    "Comment",
    "File",
    "Version",
    "Translation",
    "Language",
    "Letter Head",
    "Email Template",
    "Print Settings",
    "Customize Form",
    "Property Setter",
    "Custom Field",
]

# Shared master doctypes that need custom_company fields
SHARED_MASTER_DOCTYPES = [
    "Customer",
    "Supplier",
    "Item",
    "Price List",
    "Address",
    "Contact",
    "Item Price",
    "Brand",
    "Item Group",
    "Territory",
    "Sales Person",
    "UOM",
    "Currency",
    "Department",
    "Designation",
    "Employee",
]

# Doctypes to ignore in search_link and getdoc
IGNORE_DOCTYPES = ["Company", "User", "Module Def"]

# Layout field types that don't count as regular fields
LAYOUT_FIELD_TYPES = [
    "Tab Break",
    "Section Break",
    "Column Break",
    "Fold",
    "Page Break",
    "Heading",
    "HTML",
]

# Logging categories
LOG_CATEGORY_INSTALL = "CGF Install"
LOG_CATEGORY_UNINSTALL = "CGF Uninstall"
LOG_CATEGORY_PATCH = "CGF Patch"
LOG_CATEGORY_ERROR = "CGF Error"
LOG_CATEGORY_DEBUG = "CGF Debug"

# Cache keys
CACHE_KEY_COMPANY_FIELD = "cgf:company_field:{doctype}"
CACHE_KEY_COMPANY_FIELD_NAME = (
    "cgf:company_field_name:{doctype}"  # Stores actual field name
)
CACHE_KEY_FIRST_SECTION_FIELD = "cgf:first_section_field:{doctype}"
CACHE_KEY_USER_COMPANY = "cgf:user_company:{user}"
CACHE_TTL = 3600  # 1 hour

# Field properties
FIELD_PROPERTIES = {
    "in_list_view": 1,
    "in_standard_filter": 1,
}
