# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Patch to add custom_company fields to all doctypes
This patch ensures fields are created during migration
"""

from __future__ import unicode_literals

import frappe
from company_global_filter.constants import LOG_CATEGORY_ERROR, LOG_CATEGORY_PATCH
from company_global_filter.install import create_company_filter_fields


def execute() -> None:
    """
    Execute the patch to create company fields
    This patch ensures fields are created during migration
    """
    logger = frappe.logger("company_global_filter", allow_site=True)
    try:
        logger.info("Company Global Filter: Running patch to create company fields")
        stats = create_company_filter_fields()
        frappe.db.commit()
        logger.info(
            f"Company Global Filter: Patch completed successfully. Stats: {stats}"
        )
    except Exception as e:
        logger.error(f"Company Global Filter: Patch error - {str(e)}", exc_info=True)
        frappe.log_error(
            f"Company Global Filter: Patch error - {str(e)}", LOG_CATEGORY_ERROR
        )
        # Don't raise - allow migration to continue even if some fields fail
