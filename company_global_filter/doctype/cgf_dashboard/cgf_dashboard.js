// Copyright (c) 2025, Company Global Filter and contributors
// For license information, please see license.txt

frappe.ui.form.on("CGF Dashboard", {
	refresh: function(frm) {
		// Load dashboard data
		frappe.call({
			method: "company_global_filter.doctype.cgf_dashboard.cgf_dashboard.get_dashboard_data",
			callback: function(r) {
				if (r.message) {
					render_dashboard(r.message);
				}
			},
		});

		// Add refresh button
		frm.add_custom_button(__("Refresh"), function() {
			frm.reload_doc();
		});
	},
});

function render_dashboard(data) {
	const html = `
		<div class="cgf-dashboard-container" style="padding: 20px;">
			<div class="row">
				<div class="col-md-12">
					<h3>Company Global Filter Dashboard</h3>
					<hr>
				</div>
			</div>
			
			<div class="row">
				<div class="col-md-3">
					<div class="card" style="padding: 15px; margin-bottom: 15px;">
						<h5>Status</h5>
						<p>
							<strong>Filtering:</strong> 
							<span class="badge ${data.filtering_enabled ? 'badge-success' : 'badge-secondary'}">
								${data.filtering_enabled ? 'Enabled' : 'Disabled'}
							</span>
						</p>
						<p>
							<strong>Auto Create Fields:</strong> 
							<span class="badge ${data.auto_create_fields ? 'badge-success' : 'badge-secondary'}">
								${data.auto_create_fields ? 'Yes' : 'No'}
							</span>
						</p>
						<p><strong>Field Placement:</strong> ${data.field_placement || 'N/A'}</p>
						<p><strong>Current Company:</strong> ${data.user_company || 'None'}</p>
					</div>
				</div>
				
				<div class="col-md-3">
					<div class="card" style="padding: 15px; margin-bottom: 15px;">
						<h5>Statistics</h5>
						<p><strong>Total DocTypes:</strong> ${data.total_doctypes || 0}</p>
						<p><strong>With Company Fields:</strong> ${data.doctypes_with_fields || 0}</p>
						<p><strong>Without Fields:</strong> ${data.doctypes_without_fields || 0}</p>
						<p><strong>Filtered DocTypes:</strong> ${data.filtered_doctypes_count || 0}</p>
					</div>
				</div>
				
				<div class="col-md-3">
					<div class="card" style="padding: 15px; margin-bottom: 15px;">
						<h5>Quick Actions</h5>
						<p>
							<a href="/app/company-global-filter-settings" class="btn btn-sm btn-primary">
								Settings
							</a>
						</p>
						<p>
							<a href="/app/doctype/Custom Field" class="btn btn-sm btn-secondary">
								View Custom Fields
							</a>
						</p>
					</div>
				</div>
				
				<div class="col-md-3">
					<div class="card" style="padding: 15px; margin-bottom: 15px;">
						<h5>Excluded DocTypes</h5>
						<p>${data.excluded_doctypes ? data.excluded_doctypes.length : 0} excluded</p>
						${data.excluded_doctypes && data.excluded_doctypes.length > 0 ? 
							'<ul style="font-size: 12px;">' + 
							data.excluded_doctypes.slice(0, 5).map(d => `<li>${d}</li>`).join('') + 
							'</ul>' : 
							'<p class="text-muted">None</p>'
						}
					</div>
				</div>
			</div>
			
			<div class="row">
				<div class="col-md-6">
					<div class="card" style="padding: 15px;">
						<h5>DocTypes with Company Fields</h5>
						<ul style="max-height: 300px; overflow-y: auto;">
							${(data.doctypes_with_fields_list || []).map(d => 
								`<li><a href="/app/doctype/${d}">${d}</a> 
									${data.doctype_counts && data.doctype_counts[d] ? 
										`<span class="badge badge-secondary">${data.doctype_counts[d]} docs</span>` : 
										''
									}
								</li>`
							).join('')}
						</ul>
					</div>
				</div>
				
				<div class="col-md-6">
					<div class="card" style="padding: 15px;">
						<h5>DocTypes without Company Fields</h5>
						<ul style="max-height: 300px; overflow-y: auto;">
							${(data.doctypes_without_fields_list || []).map(d => 
								`<li><a href="/app/doctype/${d}">${d}</a></li>`
							).join('')}
						</ul>
					</div>
				</div>
			</div>
		</div>
	`;

	const dashboardElement = document.getElementById("cgf-dashboard");
	if (dashboardElement) {
		dashboardElement.innerHTML = html;
	}
}

