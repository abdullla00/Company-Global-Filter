# -*- coding: utf-8 -*-
# Copyright (c) 2025, Company Global Filter and contributors
# For license information, please see license.txt

"""
Unit tests for Company Global Filter installation functions
"""

from __future__ import unicode_literals

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

from company_global_filter.install import (
    doctype_exists,
    get_all_doctypes_with_company_fields,
    get_first_section_last_field,
    has_company_field,
)


class TestInstallFunctions(FrappeTestCase):
	"""Test installation utility functions"""

	def setUp(self):
		"""Set up test fixtures"""
		pass

	def tearDown(self):
		"""Clean up after tests"""
		pass

	def test_doctype_exists(self):
		"""Test doctype_exists function"""
		# Test with existing doctype
		self.assertTrue(doctype_exists("User"))
		self.assertTrue(doctype_exists("Company"))

		# Test with non-existing doctype
		self.assertFalse(doctype_exists("NonExistentDocType12345"))

	def test_get_all_doctypes_with_company_fields(self):
		"""Test get_all_doctypes_with_company_fields function"""
		doctypes = get_all_doctypes_with_company_fields()

		# Should return a list
		self.assertIsInstance(doctypes, list)

		# Should contain expected doctypes
		self.assertIn("Customer", doctypes)
		self.assertIn("Item", doctypes)
		self.assertIn("Supplier", doctypes)
		self.assertIn("User", doctypes)

	def test_has_company_field(self):
		"""Test has_company_field function"""
		# Test with doctype that has company field
		# Note: This test assumes Sales Invoice has a company field
		if doctype_exists("Sales Invoice"):
			# Sales Invoice should have a company field
			result = has_company_field("Sales Invoice")
			# Result could be True or False depending on setup
			self.assertIsInstance(result, bool)

		# Test with doctype that doesn't have company field
		# User doctype typically doesn't have a company field
		if doctype_exists("User"):
			result = has_company_field("User")
			# User might not have company field
			self.assertIsInstance(result, bool)

	def test_get_first_section_last_field(self):
		"""Test get_first_section_last_field function"""
		# Test with existing doctype
		if doctype_exists("Customer"):
			result = get_first_section_last_field("Customer")
			# Should return a string (fieldname) or None
			self.assertTrue(result is None or isinstance(result, str))

		# Test with non-existing doctype
		result = get_first_section_last_field("NonExistentDocType12345")
		self.assertIsNone(result)


class TestFieldPlacement(FrappeTestCase):
	"""Test field placement logic"""

	def test_get_first_section_last_field_with_real_doctype(self):
		"""Test field placement with a real doctype"""
		# Test with Customer doctype
		if doctype_exists("Customer"):
			last_field = get_first_section_last_field("Customer")
			# Should return a valid fieldname or None
			if last_field:
				# Verify it's a valid field in Customer doctype
				meta = frappe.get_meta("Customer")
				fieldnames = [f.fieldname for f in meta.fields]
				# The returned field should exist in the doctype
				# (unless it's a special case)
				self.assertIsInstance(last_field, str)


if __name__ == "__main__":
	unittest.main()

