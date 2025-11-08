# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Company Global Filter Settings DocType
Single DocType for managing app configuration
"""

from __future__ import unicode_literals

from typing import List, Optional

import frappe
from frappe.model.document import Document

from company_global_filter.constants import CACHE_TTL


class CompanyGlobalFilterSettings(Document):
	"""Company Global Filter Settings"""

	def validate(self):
		"""Validate settings"""
		# Validate cache TTL
		if self.cache_ttl and self.cache_ttl < 0:
			frappe.throw("Cache TTL must be a positive number")

		# Validate excluded doctypes (now Table field)
		if self.excluded_doctypes:
			for row in self.excluded_doctypes:
				if row.excluded_doctype and not frappe.db.exists("DocType", row.excluded_doctype):
					frappe.msgprint(
						f"Warning: DocType '{row.excluded_doctype}' does not exist in the system",
						indicator="orange",
					)
		
		# Validate excluded roles (now Table field)
		if self.excluded_roles:
			for row in self.excluded_roles:
				if row.excluded_role and not frappe.db.exists("Role", row.excluded_role):
					frappe.msgprint(
						f"Warning: Role '{row.excluded_role}' does not exist in the system",
						indicator="orange",
					)
		
		# Validate excluded users (now Table field)
		if self.excluded_users:
			for row in self.excluded_users:
				if row.excluded_user and not frappe.db.exists("User", row.excluded_user):
					frappe.msgprint(
						f"Warning: User '{row.excluded_user}' does not exist in the system",
						indicator="orange",
					)
		
		# Validate excluded companies (now Table field)
		if self.excluded_companies:
			for row in self.excluded_companies:
				if row.excluded_company and not frappe.db.exists("Company", row.excluded_company):
					frappe.msgprint(
						f"Warning: Company '{row.excluded_company}' does not exist in the system",
						indicator="orange",
					)
				# Validate visible_to_users
				if row.visible_to_users:
					for user_row in row.visible_to_users:
						if user_row.user and not frappe.db.exists("User", user_row.user):
							frappe.msgprint(
								f"Warning: User '{user_row.user}' does not exist in the system",
								indicator="orange",
							)
				# Validate visible_to_roles
				if row.visible_to_roles:
					for role_row in row.visible_to_roles:
						if role_row.role and not frappe.db.exists("Role", role_row.role):
							frappe.msgprint(
								f"Warning: Role '{role_row.role}' does not exist in the system",
								indicator="orange",
							)
		
		# Validate per-doctype excluded companies
		if self.per_doctype_excluded_companies:
			for row in self.per_doctype_excluded_companies:
				if row.target_doctype and not frappe.db.exists("DocType", row.target_doctype):
					frappe.msgprint(
						f"Warning: DocType '{row.target_doctype}' does not exist in the system",
						indicator="orange",
					)
				if row.excluded_company and not frappe.db.exists("Company", row.excluded_company):
					frappe.msgprint(
						f"Warning: Company '{row.excluded_company}' does not exist in the system",
						indicator="orange",
					)
				# Validate visible_to_users
				if row.visible_to_users:
					for user_row in row.visible_to_users:
						if user_row.user and not frappe.db.exists("User", user_row.user):
							frappe.msgprint(
								f"Warning: User '{user_row.user}' does not exist in the system",
								indicator="orange",
							)
				# Validate visible_to_roles
				if row.visible_to_roles:
					for role_row in row.visible_to_roles:
						if role_row.role and not frappe.db.exists("Role", role_row.role):
							frappe.msgprint(
								f"Warning: Role '{role_row.role}' does not exist in the system",
								indicator="orange",
							)

	def on_update(self):
		"""Clear cache when settings are updated"""
		from company_global_filter.utils import clear_company_filter_cache

		# Clear all cache to ensure new settings take effect
		clear_company_filter_cache()
		frappe.msgprint("Company Global Filter cache cleared. Settings updated successfully.")


def get_settings() -> "CompanyGlobalFilterSettings":
	"""
	Get Company Global Filter Settings
	Returns default settings if not configured
	
	Returns:
		CompanyGlobalFilterSettings document
	"""
	try:
		settings = frappe.get_single("Company Global Filter Settings")
		# Set defaults if not set
		if settings.enable_company_filtering is None:
			settings.enable_company_filtering = 1
		if settings.auto_create_fields is None:
			settings.auto_create_fields = 1
		if settings.field_placement is None:
			settings.field_placement = "First Section"
		if settings.bypass_for_system_manager is None:
			settings.bypass_for_system_manager = 1
		if settings.cache_ttl is None:
			settings.cache_ttl = 3600
		return settings
	except Exception:
		# Return default settings if not configured
		settings = frappe._dict(
			{
				"enable_company_filtering": 1,
				"auto_create_fields": 1,
				"field_placement": "First Section",
				"excluded_doctypes": [],
				"excluded_roles": [],
				"excluded_users": [],
				"excluded_companies": [],
				"per_doctype_excluded_companies": [],
				"bypass_for_system_manager": 1,
				"enable_audit_logging": 0,
				"cache_ttl": 3600,
			}
		)
		return settings


def is_filtering_enabled() -> bool:
	"""
	Check if company filtering is enabled
	
	Returns:
		True if filtering is enabled, False otherwise
	"""
	settings = get_settings()
	return bool(settings.enable_company_filtering)


def is_doctype_excluded(doctype: str) -> bool:
	"""
	Check if a doctype is excluded from filtering
	
	Args:
		doctype: Name of the doctype to check
		
	Returns:
		True if doctype is excluded, False otherwise
	"""
	settings = get_settings()
	if not settings.excluded_doctypes:
		return False

	# Handle both Table field (list of dicts) and legacy string format
	if isinstance(settings.excluded_doctypes, list):
		excluded = [row.excluded_doctype for row in settings.excluded_doctypes if hasattr(row, 'excluded_doctype') and row.excluded_doctype]
	else:
		# Legacy format: string with newlines
		excluded = [d.strip() for d in settings.excluded_doctypes.split("\n") if d.strip()]
	
	return doctype in excluded


def can_user_bypass(user: str = None) -> bool:
	"""
	Check if a user can bypass company filtering
	
	Args:
		user: Username (defaults to current user)
		
	Returns:
		True if user can bypass, False otherwise
	"""
	if not user:
		user = frappe.session.user

	settings = get_settings()

	# Check if System Manager bypass is enabled
	if settings.bypass_for_system_manager:
		if "System Manager" in frappe.get_roles(user):
			return True

	# Check excluded roles (now Table field)
	if settings.excluded_roles:
		# Handle both Table field (list of dicts) and legacy string format
		if isinstance(settings.excluded_roles, list):
			excluded_roles = [row.excluded_role for row in settings.excluded_roles if hasattr(row, 'excluded_role') and row.excluded_role]
		else:
			# Legacy format: comma-separated string
			excluded_roles = [r.strip() for r in settings.excluded_roles.split(",") if r.strip()]
		
		user_roles = frappe.get_roles(user)
		if any(role in user_roles for role in excluded_roles):
			return True

	# Check excluded users (now Table field)
	if settings.excluded_users:
		# Handle both Table field (list of dicts) and legacy string format
		if isinstance(settings.excluded_users, list):
			excluded_users = [row.excluded_user for row in settings.excluded_users if hasattr(row, 'excluded_user') and row.excluded_user]
		else:
			# Legacy format: comma-separated string
			excluded_users = [u.strip() for u in settings.excluded_users.split(",") if u.strip()]
		
		if user in excluded_users:
			return True

	return False


def _user_has_access_to_excluded_company(excluded_company_row, user: str) -> bool:
	"""
	Check if user has access to an excluded company based on visible_to_users and visible_to_roles
	
	Args:
		excluded_company_row: Row from excluded_companies or per_doctype_excluded_companies table
		user: Username to check
		
	Returns:
		True if user has access, False otherwise
	"""
	# If no visibility restrictions, allow all users (or we could default to no access)
	# For now, if no users/roles specified, we'll allow access (can be changed based on requirements)
	has_users = excluded_company_row.visible_to_users and len(excluded_company_row.visible_to_users) > 0
	has_roles = excluded_company_row.visible_to_roles and len(excluded_company_row.visible_to_roles) > 0
	
	# If no restrictions specified, allow access
	if not has_users and not has_roles:
		return True
	
	# Check user-based access
	if has_users:
		user_list = [row.user for row in excluded_company_row.visible_to_users if hasattr(row, 'user') and row.user]
		if user in user_list:
			return True
	
	# Check role-based access
	if has_roles:
		role_list = [row.role for row in excluded_company_row.visible_to_roles if hasattr(row, 'role') and row.role]
		user_roles = frappe.get_roles(user)
		if any(role in user_roles for role in role_list):
			return True
	
	return False


def is_company_excluded(company: str, doctype: str = None, user: str = None) -> bool:
	"""
	Check if a company is excluded from filtering and if user has access to it
	
	Args:
		company: Name of the company to check
		doctype: Optional doctype name (for per-doctype exclusions)
		user: Optional username (defaults to current user)
		
	Returns:
		True if company is excluded and user has access, False otherwise
	"""
	if not user:
		user = frappe.session.user if hasattr(frappe, 'session') and frappe.session else None
	
	if not user:
		return False
	
	settings = get_settings()
	
	# Check per-doctype excluded companies first (they override global)
	if doctype and settings.per_doctype_excluded_companies:
		if isinstance(settings.per_doctype_excluded_companies, list):
			for row in settings.per_doctype_excluded_companies:
				if (hasattr(row, 'target_doctype') and row.target_doctype == doctype and
					hasattr(row, 'excluded_company') and row.excluded_company == company):
					return _user_has_access_to_excluded_company(row, user)
	
	# Check global excluded companies
	if settings.excluded_companies:
		if isinstance(settings.excluded_companies, list):
			for row in settings.excluded_companies:
				if (hasattr(row, 'excluded_company') and row.excluded_company == company):
					return _user_has_access_to_excluded_company(row, user)
	
	return False


def get_excluded_companies_for_user(user: str = None, doctype: str = None) -> List[str]:
	"""
	Get list of excluded companies accessible to user
	
	Args:
		user: Optional username (defaults to current user)
		doctype: Optional doctype name (for per-doctype exclusions)
		
	Returns:
		List of company names that are excluded and accessible to user
	"""
	if not user:
		user = frappe.session.user if hasattr(frappe, 'session') and frappe.session else None
	
	if not user:
		return []
	
	# Check cache first
	cache_key = f"cgf:excluded_companies:{user}:{doctype or 'all'}"
	cached_companies = frappe.cache().get(cache_key)
	if cached_companies is not None:
		return cached_companies
	
	settings = get_settings()
	excluded_companies = []
	
	# Get per-doctype excluded companies first (they override global)
	if doctype and settings.per_doctype_excluded_companies:
		if isinstance(settings.per_doctype_excluded_companies, list):
			for row in settings.per_doctype_excluded_companies:
				if (hasattr(row, 'target_doctype') and row.target_doctype == doctype and
					hasattr(row, 'excluded_company') and row.excluded_company):
					if row.excluded_company not in excluded_companies:
						if _user_has_access_to_excluded_company(row, user):
							excluded_companies.append(row.excluded_company)
	
	# Get global excluded companies (only if not already in per-doctype list)
	if settings.excluded_companies:
		if isinstance(settings.excluded_companies, list):
			for row in settings.excluded_companies:
				if (hasattr(row, 'excluded_company') and row.excluded_company):
					if row.excluded_company not in excluded_companies:
						if _user_has_access_to_excluded_company(row, user):
							excluded_companies.append(row.excluded_company)
	
	# Cache the result
	try:
		frappe.cache().set_value(cache_key, excluded_companies, expires_in_sec=CACHE_TTL)
	except TypeError:
		# Fallback for older Frappe versions
		frappe.cache().set(cache_key, excluded_companies)
	
	return excluded_companies

