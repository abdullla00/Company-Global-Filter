from __future__ import unicode_literals

from typing import Any, Dict, Optional

import frappe
from frappe import _
from frappe.desk.form.load import getdoc as frappe_getdoc

from company_global_filter.constants import IGNORE_DOCTYPES
from company_global_filter.doctype.company_global_filter_settings.company_global_filter_settings import (
    is_company_excluded,
)
from company_global_filter.hook_functions.global_company_filter import (
    get_company_field_name,
    get_user_company,
)


@frappe.whitelist()
def getdoc(
	doctype: str,
	name: str,
	user: Optional[str] = None,
	for_edit: bool = False,
) -> Dict[str, Any]:
	"""
	Extended getdoc method that applies company filtering
	
	Args:
		doctype: Name of the doctype
		name: Name of the document
		user: Username (optional, for compatibility)
		for_edit: Whether document is being loaded for editing
		
	Returns:
		Document data dictionary
		
	Raises:
		frappe.PermissionError: If user doesn't have access to the document's company
	"""
	logger = frappe.logger("company_global_filter", allow_site=True)
	try:
		# Get user's company
		user_company = get_user_company()

		# If no user company, proceed with original getdoc
		if not user_company:
			logger.debug(f"No company found for user, skipping filter for {doctype} {name}")
			return frappe_getdoc(doctype, name)

		# Skip company filtering for ignored doctypes
		if doctype in IGNORE_DOCTYPES:
			return frappe_getdoc(doctype, name)

		# Check if doctype has company field using cached function
		company_field_name = get_company_field_name(doctype)

		# If no company field exists, proceed with original getdoc
		if not company_field_name:
			return frappe_getdoc(doctype, name)

		# Get the document
		doc = frappe.get_doc(doctype, name)

		# Check company field
		doc_company = doc.get(company_field_name)

		# If document company doesn't match user company, check if it's an excluded company
		if doc_company and doc_company != user_company:
			# Check if this company is excluded and user has access
			user = frappe.session.user if hasattr(frappe, 'session') and frappe.session else None
			if user and is_company_excluded(doc_company, doctype, user):
				logger.debug(
					f"Access granted: Document company '{doc_company}' is excluded and user '{user}' has access for {doctype} {name}"
				)
				# Company is excluded and user has access, allow document access
				return frappe_getdoc(doctype, name)
			
			# Company doesn't match and is not excluded, raise permission error
			logger.warning(
				f"Permission denied: User company '{user_company}' doesn't match document company '{doc_company}' for {doctype} {name}"
			)
			frappe.throw(
				_("You don't have permission to access this {0}. This document belongs to a different company.").format(doctype),
				frappe.PermissionError,
			)

		# If company matches or document has no company, proceed with original getdoc
		logger.debug(f"Company check passed for {doctype} {name}")
		return frappe_getdoc(doctype, name)

	except frappe.PermissionError:
		# Re-raise permission errors
		raise
	except Exception as e:
		logger = frappe.logger("company_global_filter", allow_site=True)
		logger.warning(f"Error in getdoc for {doctype} {name}: {str(e)}", exc_info=True)
		frappe.log_error(f"Error in getdoc: {str(e)}", "GetDoc Error")
		# Fallback to original getdoc on any other error
		return frappe_getdoc(doctype, name)
