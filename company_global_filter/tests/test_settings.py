# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Unit tests for Company Global Filter Settings
"""

from __future__ import unicode_literals

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

from company_global_filter.doctype.company_global_filter_settings.company_global_filter_settings import (
	can_user_bypass,
	get_settings,
	is_doctype_excluded,
	is_filtering_enabled,
)


class TestSettingsFunctions(FrappeTestCase):
	"""Test settings utility functions"""

	def setUp(self):
		"""Set up test fixtures"""
		pass

	def tearDown(self):
		"""Clean up after tests"""
		pass

	def test_get_settings(self):
		"""Test get_settings function"""
		settings = get_settings()

		# Should return a dict-like object
		self.assertIsNotNone(settings)

		# Should have expected attributes
		self.assertTrue(hasattr(settings, "enable_company_filtering"))
		self.assertTrue(hasattr(settings, "auto_create_fields"))

	def test_is_filtering_enabled(self):
		"""Test is_filtering_enabled function"""
		result = is_filtering_enabled()

		# Should return a boolean
		self.assertIsInstance(result, bool)

	def test_is_doctype_excluded(self):
		"""Test is_doctype_excluded function"""
		# Test with non-excluded doctype
		result = is_doctype_excluded("Customer")
		self.assertIsInstance(result, bool)

		# Test with potentially excluded doctype
		result = is_doctype_excluded("User")
		self.assertIsInstance(result, bool)

	def test_can_user_bypass(self):
		"""Test can_user_bypass function"""
		# Test with current user
		result = can_user_bypass()

		# Should return a boolean
		self.assertIsInstance(result, bool)

		# Test with specific user
		if frappe.db.exists("User", "Administrator"):
			result = can_user_bypass("Administrator")
			self.assertIsInstance(result, bool)


if __name__ == "__main__":
	unittest.main()

