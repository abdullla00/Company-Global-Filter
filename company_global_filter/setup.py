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


def ensure_module_exists():
    """
    Ensure Company Global Filter module exists with correct app_name.
    This must be called before creating DocTypes to ensure they are associated
    with the correct app for proper uninstall cleanup.
    """
    module_name = "Company Global Filter"
    
    if frappe.db.exists("Module Def", module_name):
        mod = frappe.get_doc("Module Def", module_name)
        if mod.app_name != "company_global_filter":
            mod.app_name = "company_global_filter"
            mod.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"✓ Updated module '{module_name}' app_name to 'company_global_filter'")
        else:
            print(f"✓ Module '{module_name}' already has correct app_name")
    else:
        mod = frappe.get_doc({
            "doctype": "Module Def",
            "module_name": module_name,
            "app_name": "company_global_filter",
            "custom": 0
        })
        mod.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"✓ Created module '{module_name}' with app_name 'company_global_filter'")


def import_doctypes():
	"""Import DocTypes from JSON files"""
	# Ensure module exists with correct app_name before creating DocTypes
	ensure_module_exists()
	
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
			# Update existing Settings DocType to ensure excluded companies fields exist
			print(f"✓ Settings DocType '{settings_doc['name']}' already exists, checking fields...")
			settings_dt = frappe.get_doc("DocType", settings_doc["name"])
			meta = frappe.get_meta(settings_doc["name"])
			
			# Check if excluded companies fields exist
			excluded_companies_field = meta.get_field("excluded_companies")
			per_doctype_field = meta.get_field("per_doctype_excluded_companies")
			
			if not excluded_companies_field or not per_doctype_field:
				# Add missing fields by directly inserting into DocField table
				json_fields = {f["fieldname"]: f for f in settings_doc["fields"]}
				fields_to_add = ["excluded_companies_section", "excluded_companies", "per_doctype_excluded_companies"]
				
				# Get max idx for existing fields
				max_idx_result = frappe.db.sql("""
					SELECT MAX(idx) as max_idx
					FROM `tabDocField`
					WHERE parent = 'Company Global Filter Settings'
				""", as_dict=True)
				max_idx = (max_idx_result[0].get("max_idx", 0) or 0) if max_idx_result else 0
				
				fields_added = 0
				for i, fieldname in enumerate(fields_to_add):
					if fieldname in json_fields:
						# Check if field already exists
						exists = frappe.db.exists("DocField", {
							"parent": "Company Global Filter Settings",
							"fieldname": fieldname
						})
						
						if not exists:
							field_data = json_fields[fieldname]
							# Create DocField document
							new_field = frappe.get_doc({
								"doctype": "DocField",
								"parent": "Company Global Filter Settings",
								"parenttype": "DocType",
								"parentfield": "fields",
								"idx": max_idx + i + 1,
							})
							# Update with field data from JSON
							for key, value in field_data.items():
								if key not in ["doctype", "name", "idx"]:
									setattr(new_field, key, value)
							
							new_field.insert(ignore_permissions=True)
							fields_added += 1
							print(f"  Added field: {fieldname}")
				
				if fields_added > 0:
					frappe.db.commit()
					
					# Update field_order in DocType
					settings_dt = frappe.get_doc("DocType", settings_doc["name"])
					if "field_order" in settings_doc:
						settings_dt.field_order = json.dumps(settings_doc["field_order"])
						settings_dt.save(ignore_permissions=True)
						frappe.db.commit()
					
					# Clear cache
					frappe.clear_cache()
					
					# Verify fields are visible in meta
					meta = frappe.get_meta("Company Global Filter Settings")
					excluded_companies_field = meta.get_field("excluded_companies")
					per_doctype_field = meta.get_field("per_doctype_excluded_companies")
					
					if excluded_companies_field and per_doctype_field:
						print(f"  ✓ Verified: excluded_companies and per_doctype_excluded_companies fields are visible in meta")
					else:
						print(f"  ⚠ Warning: Fields may not be visible in meta after cache clear")
			else:
				print(f"✓ Excluded companies fields already exist")
			
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

