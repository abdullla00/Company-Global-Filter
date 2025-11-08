# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Company Global Filter Dashboard
Shows statistics and information about filtered doctypes
"""

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class CGFDashboard(Document):
	"""Company Global Filter Dashboard"""

	pass


@frappe.whitelist()
def get_dashboard_data():
	"""
	Get dashboard statistics and data
	
	Returns:
		Dict with dashboard statistics
	"""
	from company_global_filter.doctype.company_global_filter_settings.company_global_filter_settings import (
		get_excluded_companies_for_user,
		get_settings,
		is_filtering_enabled,
	)
	from company_global_filter.install import get_all_doctypes_with_company_fields
	from company_global_filter.hook_functions.global_company_filter import (
		get_company_field_name,
	)
	from company_global_filter.utils import get_filtered_doctypes

	try:
		settings = get_settings()
		all_doctypes = get_all_doctypes_with_company_fields()
		filtered_doctypes = get_filtered_doctypes()

		# Count doctypes with company fields
		doctypes_with_fields = []
		doctypes_without_fields = []

		for doctype in all_doctypes:
			if get_company_field_name(doctype):
				doctypes_with_fields.append(doctype)
			else:
				doctypes_without_fields.append(doctype)

		# Get user company
		from company_global_filter.hook_functions.global_company_filter import (
			get_user_company,
		)

		user_company = get_user_company()

		# Get excluded companies for current user
		user = frappe.session.user if hasattr(frappe, 'session') and frappe.session else None
		excluded_companies = get_excluded_companies_for_user(user) if user else []
		
		# Count excluded companies (global and per-doctype)
		global_excluded_companies_count = 0
		global_excluded_companies_list = []
		if settings.excluded_companies and isinstance(settings.excluded_companies, list):
			global_excluded_companies_count = len(settings.excluded_companies)
			global_excluded_companies_list = [
				row.excluded_company for row in settings.excluded_companies 
				if hasattr(row, 'excluded_company') and row.excluded_company
			]
		
		per_doctype_excluded_companies_count = 0
		per_doctype_excluded_companies_list = []
		if settings.per_doctype_excluded_companies and isinstance(settings.per_doctype_excluded_companies, list):
			per_doctype_excluded_companies_count = len(settings.per_doctype_excluded_companies)
			per_doctype_excluded_companies_list = [
				{"doctype": row.target_doctype, "company": row.excluded_company}
				for row in settings.per_doctype_excluded_companies
				if hasattr(row, 'target_doctype') and hasattr(row, 'excluded_company') and row.target_doctype and row.excluded_company
			]

		# Count documents per doctype (sample)
		doctype_counts = {}
		for doctype in doctypes_with_fields[:10]:  # Limit to first 10 for performance
			try:
				count = frappe.db.count(doctype)
				doctype_counts[doctype] = count
			except Exception:
				doctype_counts[doctype] = 0

		return {
			"filtering_enabled": is_filtering_enabled(),
			"auto_create_fields": settings.auto_create_fields,
			"field_placement": settings.field_placement,
			"total_doctypes": len(all_doctypes),
			"doctypes_with_fields": len(doctypes_with_fields),
			"doctypes_without_fields": len(doctypes_without_fields),
			"filtered_doctypes_count": len(filtered_doctypes),
			"doctypes_with_fields_list": doctypes_with_fields[:20],  # Limit for display
			"doctypes_without_fields_list": doctypes_without_fields[:20],
			"user_company": user_company,
			"doctype_counts": doctype_counts,
			"excluded_doctypes": (
				[row.excluded_doctype for row in settings.excluded_doctypes if hasattr(row, 'excluded_doctype') and row.excluded_doctype]
				if settings.excluded_doctypes and isinstance(settings.excluded_doctypes, list)
				else (
					settings.excluded_doctypes.split("\n")
					if settings.excluded_doctypes
					else []
				)
			),
			"excluded_companies_count": len(excluded_companies),
			"excluded_companies_list": excluded_companies,
			"global_excluded_companies_count": global_excluded_companies_count,
			"global_excluded_companies_list": global_excluded_companies_list[:20],  # Limit for display
			"per_doctype_excluded_companies_count": per_doctype_excluded_companies_count,
			"per_doctype_excluded_companies_list": per_doctype_excluded_companies_list[:20],  # Limit for display
		}

	except Exception as e:
		frappe.log_error(f"Error getting dashboard data: {str(e)}", "CGF Dashboard Error")
		return {
			"error": str(e),
			"filtering_enabled": False,
			"total_doctypes": 0,
			"doctypes_with_fields": 0,
		}

