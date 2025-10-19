# Company Global Filter

A comprehensive Frappe/ERPNext application that automatically applies company-level filters across all doctypes to ensure users only see records relevant to their assigned company.

## Overview

Company Global Filter automatically applies company-level security filters across your entire ERPNext instance. This ensures that users only see and interact with records that belong to their assigned company, simplifying multi-company management and improving data security.

## Features

### 🔒 Global Company Filtering
- **Automatic Permission Filtering**: Applies company filters to all doctypes with company fields
- **Session-based Company Selection**: Users can switch between companies they have access to
- **Multi-company Support**: Perfect for organizations managing multiple companies in one ERPNext instance

### 🎯 Smart Detection
- Automatically detects doctypes with `company` or `custom_company` fields
- Skips system doctypes to prevent performance issues
- Fallback mechanisms to ensure system stability

### 👤 User-Friendly Interface
- Company selector in navbar for quick switching
- Visual indication of current company
- Search functionality within company dropdown

### 🔧 Technical Features
- Overrides core Frappe methods (`search_link`, `getdoc`) for seamless integration
- Permission query conditions for database-level filtering
- Robust error handling to prevent system crashes

## Installation

1. **Install the app**:
   ```bash
   bench get-app company_global_filter
   bench --site your-site.local install-app company_global_filter
   ```
2. **Required Setup**:

- Ensure all users have a default company set in their user preferences
- Make sure all relevant doctypes have proper company field configurations

## Configuration

### User Default Company
Set default company for users via:
- **User Document**: Set default company in user master
- **Session Defaults**: Users can switch companies via navbar dropdown

### Doctype Requirements
The app automatically filters doctypes that have:
- A standard `company` field (type: Link, options: Company)
- A custom `custom_company` field (type: Link, options: Company)

## Usage

### For End Users
- **Company Selection**: Use the company dropdown in the navbar to switch between companies
- **Automatic Filtering**: All lists, reports, and searches will automatically filter by selected company
- **Visual Feedback**: The navbar displays the currently active company

### For Administrators
- **User Management**: Ensure each user has appropriate company access
- **Doctype Setup**: Verify company fields exist in relevant doctypes
- **Troubleshooting**: Check error logs for any permission issues

## API Methods

### `get_company_list()`
Returns list of all companies accessible to the current user.

### `set_selected_company(company)`
Sets the user's selected company in session.

### `get_selected_company()`
Returns the user's currently selected company information.

### `clear_selected_company()`
Clears the user's selected company from session.

### `get_permission_query_conditions(user, doctype)`
Applies company filters to permission queries (automatically used by Frappe).

## Technical Implementation

### Overridden Methods
- **`search_link`**: Applies company filters to link field searches
- **`getdoc`**: Validates company permissions when loading documents
- **Permission System**: Adds company conditions to all SQL queries

### Security Features
- Database-level filtering prevents unauthorized data access
- Graceful error handling maintains system stability
- Session-based company validation

## Customization

### Adding Company Fields
To enable filtering for a custom doctype:

```python
# Add either standard company field
company = frappe.get_meta("Your Doctype").get_field("company")

# Or custom company field
custom_company = frappe.get_meta("Your Doctype").get_field("custom_company")
```
## Excluding Doctypes

The app automatically excludes system doctypes. To manually exclude additional doctypes, modify the `system_doctypes` list in the permission query function.

## Troubleshooting

### Common Issues

#### No Company Filter Applied
- Check if doctype has proper company field
- Verify user has default company set
- Check error logs for permission query issues

#### Performance Issues
- The app includes optimizations to skip system doctypes
- Monitor database queries for any bottlenecks

#### Permission Errors
- Verify user has access to the company they're trying to view
- Check if document has company field populated

### Debugging

Enable debug logging to track company filtering:

```python
frappe.log_error("Debug info", "Company Filter Debug")
```
## Support

For issues and feature requests, contact:

- **Email**: munim@invento.com.bd
- **Publisher**: Invento Software Limited

## License

MIT License
