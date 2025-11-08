# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Unit tests for Company Global Filter core functions
"""

from __future__ import unicode_literals

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

from company_global_filter.hook_functions.global_company_filter import (
	get_company_field_name,
	get_permission_query_conditions,
	get_user_company,
)


class TestGlobalFilterFunctions(FrappeTestCase):
	"""Test global filter utility functions"""

	def setUp(self):
		"""Set up test fixtures"""
		pass

	def tearDown(self):
		"""Clean up after tests"""
		pass

	def test_get_user_company(self):
		"""Test get_user_company function"""
		result = get_user_company()

		# Should return a string (company name) or None
		self.assertTrue(result is None or isinstance(result, str))

	def test_get_company_field_name(self):
		"""Test get_company_field_name function"""
		# Test with doctype that has company field
		if frappe.db.exists("DocType", "Sales Invoice"):
			result = get_company_field_name("Sales Invoice")
			# Should return 'company' or None
			self.assertTrue(result is None or result in ["company", "custom_company"])

		# Test with doctype that doesn't have company field
		result = get_company_field_name("User")
		# Should return None or a field name
		self.assertTrue(result is None or isinstance(result, str))

	def test_get_permission_query_conditions(self):
		"""Test get_permission_query_conditions function"""
		# Test with None doctype
		result = get_permission_query_conditions("Administrator", None)
		self.assertEqual(result, "")

		# Test with valid doctype
		if frappe.db.exists("DocType", "Customer"):
			result = get_permission_query_conditions("Administrator", "Customer")
			# Should return a string (SQL condition or empty)
			self.assertIsInstance(result, str)

		# Test with system doctype (should return empty)
		result = get_permission_query_conditions("Administrator", "User")
		self.assertEqual(result, "")


if __name__ == "__main__":
	unittest.main()

