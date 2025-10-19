frappe.templates.navbar = `
    <header class="navbar navbar-expand sticky-top" role="navigation">
        <div class="container">
          <a class="navbar-brand navbar-home" href="/app">
            <img
              class="app-logo"
              style="width: {{ navbar_settings.logo_width || 60 }}px"
              src="{{ frappe.boot.app_logo_url }}"
              alt="{{ __("App Logo") }}"
            >
          </a>
          <ul class="nav navbar-nav d-none d-sm-flex" id="navbar-breadcrumbs"></ul>
          <div class="collapse navbar-collapse justify-content-end">
			<form class="form-inline fill-width justify-content-end" role="search" onsubmit="return false;">
				{% if (frappe.boot.read_only) { %}
					<span class="indicator-pill yellow no-indicator-dot read-only-banner" title="{%= __("Your site is undergoing maintenance or being updated.") %}">
						{%= __("Read Only Mode") %}
					</span>
				{% } %}
				{% if (frappe.boot.user.impersonated_by) { %}
					<span class="indicator-pill red no-indicator-dot" title="{%= __("You are impersonating as another user.") %}">
						{%= __("Impersonating {0}", [frappe.boot.user.name]) %}
					</span>
				{% } %}
				<div class="input-group search-bar text-muted hidden">
					<input
						id="navbar-search"
						type="text"
						class="form-control"
						placeholder="{%= __('Search or type a command ({0})', [frappe.utils.is_mac() ? '⌘ + G' : 'Ctrl + G']) %}"
						aria-haspopup="true"
					>
					<span class="search-icon">
						<svg class="icon icon-sm"><use href="#icon-search"></use></svg>
					</span>
				</div>
			</form>
			<ul class="navbar-nav">
				<li class="nav-item dropdown dropdown-notifications dropdown-mobile hidden">
					<button
						class="btn-reset nav-link notifications-icon text-muted"
						data-toggle="dropdown"
						aria-haspopup="true"
						aria-expanded="false"
					>
						<span class="notifications-seen">
							<span class="sr-only">{{ __("No new notifications") }}</span>
							<svg class="es-icon icon-sm" style="stroke:none;"><use href="#es-line-notifications"></use></svg>
						</span>
						<span class="notifications-unseen">
							<span class="sr-only">{{ __("You have unseen notifications") }}</span>
							<svg class="es-icon icon-sm"><use href="#es-line-notifications-unseen"></use></svg>
						</span>
					</button>
					<div class="dropdown-menu notifications-list dropdown-menu-right" role="menu">
						<div class="notification-list-header">
							<div class="header-items"></div>
							<div class="header-actions"></div>
						</div>
						<div class="notification-list-body">
							<div class="panel-notifications"></div>
							<div class="panel-events"></div>
						</div>
					</div>
				</li>
				<li class="nav-item dropdown dropdown-message dropdown-mobile hidden">
					<button
						class="btn-reset nav-link notifications-icon text-muted"
						data-toggle="dropdown"
						aria-haspopup="true"
						aria-expanded="true"
					>
						<span>
							<svg class="es-icon icon-sm"><use href="#es-line-chat-alt"></use></svg>
						</span>
					</button>
				</li>
				<li class="vertical-bar d-none d-sm-block"></li>
				<li class="nav-item dropdown dropdown-mobile d-none d-lg-block">
					<button
						class="btn btn-primary"
						data-toggle="dropdown"
						aria-controls="toolbar-company"
					>
						{% if frappe.defaults.get_user_default("Company") %}
							{{ frappe.defaults.get_user_default("Company") }}
						{% else %}
							{{ __("Select Company") }}
						{% endif %}
					</button>

					<div class="dropdown-menu dropdown-menu-right" id="toolbar-company" role="menu">
						<div class="p-2">
							<input
								type="text"
								class="form-control"
								placeholder="Search Company"
								id="company-search"
							/>
						</div>
						<div id="company-list" class="company-list-scrollable px-2"></div>
					</div>
				</li>
				<li class="vertical-bar d-none d-sm-block"></li>
				<li class="nav-item dropdown dropdown-help dropdown-mobile d-none d-lg-block">
					<button
						class="btn-reset nav-link"
						data-toggle="dropdown"
						aria-controls="toolbar-help"
						aria-label="{{ __("Help Dropdown") }}"
					>
						<span>
							{{ __("Help") }}
							<svg class="es-icon icon-xs"><use href="#es-line-down"></use></svg>
						</span>
					</button>
					<div class="dropdown-menu dropdown-menu-right" id="toolbar-help" role="menu">
						<div id="help-links"></div>
						<div class="dropdown-divider documentation-links"></div>
						{% for item in navbar_settings.help_dropdown %}
							{% if (!item.hidden) { %}
								{% if (item.route) { %}
									<a class="dropdown-item" href="{{ item.route }}">
										{%= __(item.item_label) %}
									</a>
								{% } else if (item.action) { %}
									<button class="btn-reset dropdown-item" onclick="return {{ item.action }}">
										{%= __(item.item_label) %}
									</button>
								{% } else { %}
									<div class="dropdown-divider"></div>
								{% } %}
							{% } %}
						{% endfor %}
					</div>
				</li>
				<li class="nav-item dropdown dropdown-navbar-user dropdown-mobile">
					<button
						class="btn-reset nav-link"
						data-toggle="dropdown"
						aria-label="{{ __("User Menu") }}"
					>
						{{ avatar }}
					</button>
					<div class="dropdown-menu dropdown-menu-right" id="toolbar-user" role="menu">
						{% for item in navbar_settings.settings_dropdown %}
							{% if (!item.hidden) { %}
								{% if (item.route) { %}
									<a class="dropdown-item" href="{{ item.route }}">
										{%= __(item.item_label) %}
									</a>
								{% } else if (item.action) { %}
									<button class="btn-reset dropdown-item" onclick="return {{ item.action }}">
										{%= __(item.item_label) %}
									</button>
								{% } else { %}
									<div class="dropdown-divider"></div>
								{% } %}
							{% } %}
						{% endfor %}
					</div>
				</li>
			</ul>
		  </div>
        </div>
    </header>
  `;

frappe.after_ajax(() => {
	frappe
		.call("company_global_filter.hook_functions.global_company_filter.get_company_list")
		.then((r) => {
			const companies = r.message || [];
			const container = document.getElementById("company-list");
			const searchInput = document.getElementById("company-search");

			if (!container || !searchInput) return;

			function renderList(filteredCompanies) {
				container.innerHTML = "";

				if (!filteredCompanies.length) {
					container.innerHTML =
						'<div class="text-muted small px-2 py-1">No matching companies</div>';
					return;
				}

				filteredCompanies.forEach((company_name) => {
					const btn = document.createElement("button");
					btn.className = "btn-reset dropdown-item";
					btn.textContent = company_name;
					btn.onclick = () => {
						frappe.call({
							method: "frappe.core.doctype.session_default_settings.session_default_settings.set_session_default_values",
							args: {
								default_values: { company: company_name },
							},
							callback: function (data2) {
								if (data2.message == "success") {
									frappe.show_alert({
										message: __("Session Defaults Saved"),
										indicator: "green",
									});
									frappe.ui.toolbar.clear_cache();
								} else {
									frappe.show_alert({
										message: __(
											"An error occurred while setting Session Defaults"
										),
										indicator: "red",
									});
								}
							},
						});
					};
					container.appendChild(btn);
				});
			}

			renderList(companies);

			searchInput.addEventListener("input", () => {
				const value = searchInput.value.toLowerCase();
				const filtered = companies.filter((name) => name.toLowerCase().includes(value));
				renderList(filtered);
			});
		});
});
