/**
 * Real Estate Portfolio Dashboard — Frappe Desk Page
 * Renders charts using frappe-charts (bundled with Frappe v15).
 */
frappe.pages['real-estate-dashboard'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Real Estate Portfolio Dashboard'),
		single_column: true,
	});

	page.add_action_item(__('Refresh'), () => render_dashboard(page));
	render_dashboard(page);
};

function render_dashboard(page) {
	frappe.call({
		method: 'real_estate.utils.dashboard_data.get_dashboard_data',
		callback: r => {
			if (!r.message) return;
			const data = r.message;
			page.main.html(`
				<div class="re-dashboard">
					${kpi_cards(data.kpis)}
					<div class="row mt-4">
						<div class="col-md-4">${occupancy_donut(data.occupancy)}</div>
						<div class="col-md-8">${revenue_bar_placeholder()}</div>
					</div>
					<div class="row mt-4">
						<div class="col-md-6">${expiring_leases_table(data.expiring_leases)}</div>
						<div class="col-md-6">${maintenance_kpis(data.maintenance)}</div>
					</div>
					<div class="row mt-4">
						<div class="col-12">${ai_query_widget()}</div>
					</div>
				</div>
			`);

			// Render Frappe Charts
			if (data.occupancy) render_occupancy_chart(data.occupancy);
			if (data.monthly_revenue) render_revenue_chart(data.monthly_revenue);

			// Wire AI query
			page.main.find('#re-ask-btn').on('click', () => {
				const q = page.main.find('#re-question').val();
				if (!q) return;
				ask_portfolio_ai(q, page);
			});
			page.main.find('#re-question').on('keydown', e => {
				if (e.key === 'Enter') page.main.find('#re-ask-btn').trigger('click');
			});
		},
	});
}

function kpi_cards(kpis) {
	if (!kpis) return '';
	return `
		<div class="row">
			${kpi_card(__('Total Properties'), kpis.properties, 'fa-building', '#4CAF50')}
			${kpi_card(__('Occupied Units'), kpis.occupied + ' / ' + kpis.total_units, 'fa-key', '#2196F3')}
			${kpi_card(__('Occupancy Rate'), kpis.occupancy_rate + '%', 'fa-pie-chart', '#FF9800')}
			${kpi_card(__('Overdue Invoices'), kpis.overdue_invoices, 'fa-exclamation-circle', '#F44336')}
			${kpi_card(__('Open Maintenance'), kpis.open_maintenance, 'fa-wrench', '#9C27B0')}
		</div>`;
}

function kpi_card(label, value, icon, color) {
	return `
		<div class="col">
			<div class="card text-center p-3 mb-2" style="border-top:3px solid ${color}">
				<div class="h4 mb-1" style="color:${color}"><i class="fa ${icon}"></i></div>
				<div class="h3 font-weight-bold">${value ?? '—'}</div>
				<div class="text-muted small">${label}</div>
			</div>
		</div>`;
}

function occupancy_donut(occ) {
	return `
		<div class="card p-3">
			<h6 class="card-title">${__('Occupancy Breakdown')}</h6>
			<div id="re-occupancy-chart"></div>
		</div>`;
}

function revenue_bar_placeholder() {
	return `
		<div class="card p-3">
			<h6 class="card-title">${__('Monthly Revenue (Last 6 Months)')}</h6>
			<div id="re-revenue-chart"></div>
		</div>`;
}

function render_occupancy_chart(occ) {
	if (!occ || typeof frappe.Chart === 'undefined') return;
	new frappe.Chart('#re-occupancy-chart', {
		type: 'donut',
		data: {
			labels: [__('Occupied'), __('Available'), __('Reserved'), __('Under Renovation')],
			datasets: [{ values: [occ.occupied, occ.available, occ.reserved, occ.renovation] }],
		},
		colors: ['#4CAF50', '#2196F3', '#FF9800', '#9E9E9E'],
		height: 220,
	});
}

function render_revenue_chart(monthly) {
	if (!monthly || typeof frappe.Chart === 'undefined') return;
	new frappe.Chart('#re-revenue-chart', {
		type: 'bar',
		data: {
			labels: monthly.labels,
			datasets: [{ name: __('Revenue'), values: monthly.values, chartType: 'bar' }],
		},
		colors: ['#4CAF50'],
		height: 220,
		barOptions: { spaceRatio: 0.3 },
	});
}

function expiring_leases_table(leases) {
	if (!leases || !leases.length) {
		return `<div class="card p-3"><h6>${__('Expiring Leases (next 60 days)')}</h6>
			<p class="text-muted">${__('None expiring in next 60 days')}</p></div>`;
	}
	const rows = leases.map(l => `
		<tr>
			<td>${frappe.utils.get_form_link("Lease Agreement", l.name, true, frappe.utils.escape_html(l.name))}</td>
			<td>${l.property_unit}</td>
			<td>${l.tenant}</td>
			<td><span class="badge badge-${l.days_left <= 15 ? 'danger' : 'warning'}">${l.days_left}d</span></td>
		</tr>`).join('');
	return `
		<div class="card p-3">
			<h6 class="card-title">${__('Expiring Leases (next 60 days)')}</h6>
			<table class="table table-sm">
				<thead><tr><th>${__('Lease')}</th><th>${__('Unit')}</th><th>${__('Tenant')}</th><th>${__('Days Left')}</th></tr></thead>
				<tbody>${rows}</tbody>
			</table>
		</div>`;
}

function maintenance_kpis(m) {
	if (!m) return '';
	const funnel_items = [
		{ label: __('Open'), value: m.open, color: '#FF9800' },
		{ label: __('Assigned'), value: m.assigned, color: '#2196F3' },
		{ label: __('In Progress'), value: m.in_progress, color: '#9C27B0' },
		{ label: __('Completed (30d)'), value: m.completed_30d, color: '#4CAF50' },
	];
	const bars = funnel_items.map(f => `
		<div class="d-flex align-items-center mb-2">
			<div style="width:120px" class="text-muted small">${f.label}</div>
			<div class="flex-grow-1 bg-light rounded" style="height:18px">
				<div style="width:${Math.min((f.value / (m.open || 1)) * 100, 100)}%;background:${f.color};height:18px;border-radius:4px"></div>
			</div>
			<div style="width:40px;text-align:right" class="small font-weight-bold">${f.value}</div>
		</div>`).join('');
	return `
		<div class="card p-3">
			<h6 class="card-title">${__('Maintenance KPIs')}</h6>
			${bars}
		</div>`;
}

function ai_query_widget() {
	return `
		<div class="card p-3">
			<h6 class="card-title">${__('Ask About Your Portfolio')} <span class="badge badge-info">AI</span></h6>
			<div class="input-group mb-2">
				<input id="re-question" type="text" class="form-control"
					placeholder="${__('e.g. Which units have been vacant for more than 30 days?')}">
				<div class="input-group-append">
					<button id="re-ask-btn" class="btn btn-primary">${__('Ask')}</button>
				</div>
			</div>
			<div id="re-ai-answer" class="mt-2 p-2 bg-light rounded" style="min-height:60px;white-space:pre-wrap;display:none"></div>
		</div>`;
}

function ask_portfolio_ai(question, page) {
	const $answer = page.main.find('#re-ai-answer');
	$answer.show().text(__('Thinking…'));
	frappe.call({
		method: 'real_estate.ai.portfolio_query.ask_portfolio',
		args: { question },
		callback: r => {
			$answer.text(r.message || __('No answer returned.'));
		},
	});
}
