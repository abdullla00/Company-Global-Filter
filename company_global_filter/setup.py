# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Setup utilities for Company Global Filter
"""

from __future__ import unicode_literals

import json
import os

import frappe


def import_doctypes():
	"""Import DocTypes from JSON files"""
	results = []
	
	# Create child table DocTypes first
	child_tables = [
		("cgf_excluded_doctype", "CGF Excluded DocType"),
		("cgf_excluded_role", "CGF Excluded Role"),
		("cgf_excluded_user", "CGF Excluded User"),
		("cgf_excluded_company_user", "CGF Excluded Company User"),
		("cgf_excluded_company_role", "CGF Excluded Company Role"),
		("cgf_excluded_company", "CGF Excluded Company"),
		("cgf_per_doctype_excluded_company", "CGF Per DocType Excluded Company"),
	]
	
	app_path = frappe.get_app_path("company_global_filter")
	
	for folder_name, doctype_name in child_tables:
		child_path = os.path.join(
			app_path,
			"doctype",
			folder_name,
			f"{folder_name}.json",
		)
		
		if os.path.exists(child_path):
			with open(child_path, 'r') as f:
				child_doc = json.load(f)
			
			if not frappe.db.exists("DocType", child_doc["name"]):
				print(f"Creating child table DocType: {child_doc['name']}")
				doc = frappe.get_doc(child_doc)
				doc.insert(ignore_permissions=True, ignore_links=True)
				frappe.db.commit()
				print(f"✓ Child table DocType '{child_doc['name']}' created successfully")
				results.append(True)
			else:
				print(f"✓ Child table DocType '{child_doc['name']}' already exists")
				results.append(False)
	
	# Create Settings DocType
	settings_path = os.path.join(
		app_path,
		"doctype",
		"company_global_filter_settings",
		"company_global_filter_settings.json",
	)
	
	if os.path.exists(settings_path):
		with open(settings_path, 'r') as f:
			settings_doc = json.load(f)
		
		# Check if it exists
		if not frappe.db.exists("DocType", settings_doc["name"]):
			print(f"Creating DocType: {settings_doc['name']}")
			doc = frappe.get_doc(settings_doc)
			doc.insert(ignore_permissions=True, ignore_links=True)
			frappe.db.commit()
			print(f"✓ Settings DocType '{settings_doc['name']}' created successfully")
			results.append(True)
		else:
			print(f"✓ Settings DocType '{settings_doc['name']}' already exists")
			results.append(False)
	else:
		print(f"✗ File not found: {settings_path}")
		results.append(False)

	# Create Dashboard DocType
	dashboard_path = os.path.join(
		app_path,
		"doctype",
		"cgf_dashboard",
		"cgf_dashboard.json",
	)
	
	if os.path.exists(dashboard_path):
		with open(dashboard_path, 'r') as f:
			dashboard_doc = json.load(f)
		
		# Check if it exists
		if not frappe.db.exists("DocType", dashboard_doc["name"]):
			print(f"Creating DocType: {dashboard_doc['name']}")
			doc = frappe.get_doc(dashboard_doc)
			doc.insert(ignore_permissions=True, ignore_links=True)
			frappe.db.commit()
			print(f"✓ Dashboard DocType '{dashboard_doc['name']}' created successfully")
			results.append(True)
		else:
			print(f"✓ Dashboard DocType '{dashboard_doc['name']}' already exists")
			results.append(False)
	else:
		print(f"✗ File not found: {dashboard_path}")
		results.append(False)
	
	return results

