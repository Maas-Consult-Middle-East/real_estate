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
				<div class="re-dashboard container-fluid py-3">
					${kpi_cards(data.kpis)}
					<div class="row mt-4">
						<div class="col-md-4">${occupancy_donut_html()}</div>
						<div class="col-md-8">${revenue_bar_html()}</div>
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

			render_occupancy_chart(data.occupancy);
			render_revenue_chart(data.monthly_revenue);

			page.main.find('#re-ask-btn').on('click', () => {
				const q = page.main.find('#re-question').val().trim();
				if (q) ask_portfolio_ai(q, page);
			});
			page.main.find('#re-question').on('keydown', e => {
				if (e.key === 'Enter') page.main.find('#re-ask-btn').trigger('click');
			});
		},
	});
}

function kpi_cards(kpis) {
	if (!kpis) return '';
	const cards = [
		{ label: __('Total Properties'), value: kpis.properties, icon: 'fa-building', color: '#4CAF50' },
		{ label: __('Occupied / Total'), value: `${kpis.occupied} / ${kpis.total_units}`, icon: 'fa-key', color: '#2196F3' },
		{ label: __('Occupancy Rate'), value: `${kpis.occupancy_rate}%`, icon: 'fa-pie-chart', color: '#FF9800' },
		{ label: __('Overdue Invoices'), value: kpis.overdue_invoices, icon: 'fa-exclamation-circle', color: '#F44336' },
		{ label: __('Open Maintenance'), value: kpis.open_maintenance, icon: 'fa-wrench', color: '#9C27B0' },
	];
	return `<div class="row g-3">${cards.map(c => `
		<div class="col">
			<div class="card text-center p-3 h-100" style="border-top:4px solid ${c.color}">
				<div style="color:${c.color};font-size:1.5rem"><i class="fa ${c.icon}"></i></div>
				<div style="font-size:1.6rem;font-weight:700">${c.value ?? '—'}</div>
				<div class="text-muted" style="font-size:.8rem">${c.label}</div>
			</div>
		</div>`).join('')}</div>`;
}

function occupancy_donut_html() {
	return `<div class="card p-3 h-100">
		<h6 class="card-title">${__('Occupancy Breakdown')}</h6>
		<div id="re-occupancy-chart"></div>
	</div>`;
}

function revenue_bar_html() {
	return `<div class="card p-3 h-100">
		<h6 class="card-title">${__('Monthly Revenue (Last 6 Months)')}</h6>
		<div id="re-revenue-chart"></div>
	</div>`;
}

function render_occupancy_chart(occ) {
	if (!occ || !document.getElementById('re-occupancy-chart')) return;
	new frappe.Chart('#re-occupancy-chart', {
		type: 'donut',
		data: {
			labels: [__('Occupied'), __('Available'), __('Reserved'), __('Under Renovation')],
			datasets: [{ values: [occ.occupied, occ.available, occ.reserved, occ.under_renovation] }],
		},
		colors: ['#4CAF50', '#2196F3', '#FF9800', '#9E9E9E'],
		height: 250,
	});
}

function render_revenue_chart(monthly) {
	if (!monthly || !document.getElementById('re-revenue-chart')) return;
	new frappe.Chart('#re-revenue-chart', {
		type: 'bar',
		data: {
			labels: monthly.labels,
			datasets: [{ name: __('Revenue'), values: monthly.values, chartType: 'bar' }],
		},
		colors: ['#4CAF50'],
		height: 250,
		barOptions: { spaceRatio: 0.3 },
	});
}

function expiring_leases_table(leases) {
	if (!leases || !leases.length) {
		return `<div class="card p-3 h-100"><h6 class="card-title">${__('Expiring Leases (60 days)')}</h6>
			<p class="text-muted">${__('None expiring in next 60 days')}</p></div>`;
	}
	const rows = leases.map(l => `<tr>
		<td>${frappe.utils.get_form_link("Lease Agreement", l.name, true, frappe.utils.escape_html(l.name))}</td>
		<td>${l.property_unit}</td>
		<td>${l.tenant}</td>
		<td><span class="badge" style="background:${l.days_left <= 15 ? '#F44336' : '#FF9800'};color:#fff">${l.days_left}d</span></td>
	</tr>`).join('');
	return `<div class="card p-3 h-100">
		<h6 class="card-title">${__('Expiring Leases (60 days)')}</h6>
		<table class="table table-sm mb-0">
			<thead><tr><th>${__('Lease')}</th><th>${__('Unit')}</th><th>${__('Tenant')}</th><th>${__('Left')}</th></tr></thead>
			<tbody>${rows}</tbody>
		</table>
	</div>`;
}

function maintenance_kpis(m) {
	if (!m) return '';
	const max_val = Math.max(m.open, 1);
	const items = [
		{ label: __('Open'), value: m.open, color: '#FF9800' },
		{ label: __('Assigned'), value: m.assigned, color: '#2196F3' },
		{ label: __('In Progress'), value: m.in_progress, color: '#9C27B0' },
		{ label: __('Completed (30d)'), value: m.completed_30d, color: '#4CAF50' },
	];
	const bars = items.map(f => `
		<div class="d-flex align-items-center mb-2">
			<div style="width:130px;font-size:.85rem" class="text-muted">${f.label}</div>
			<div class="flex-grow-1 bg-light rounded" style="height:16px;overflow:hidden">
				<div style="width:${Math.min((f.value / max_val) * 100, 100)}%;background:${f.color};height:16px;border-radius:4px;transition:width .4s"></div>
			</div>
			<div style="width:36px;text-align:right;font-weight:700;font-size:.9rem">${f.value}</div>
		</div>`).join('');
	return `<div class="card p-3 h-100">
		<h6 class="card-title">${__('Maintenance Pipeline')}</h6>
		${bars}
	</div>`;
}

function ai_query_widget() {
	return `<div class="card p-3">
		<h6 class="card-title">${__('Ask About Your Portfolio')}
			<span style="background:#2196F3;color:#fff;padding:2px 8px;border-radius:10px;font-size:.75rem;margin-left:6px">AI</span>
		</h6>
		<p class="text-muted small">${__('Examples: "Which units have been vacant for more than 30 days?" · "Show tenants with overdue payments" · "How many leases expire this quarter?"')}</p>
		<div class="input-group">
			<input id="re-question" type="text" class="form-control" placeholder="${__('Ask a question about your portfolio…')}">
			<div class="input-group-append">
				<button id="re-ask-btn" class="btn btn-primary">${__('Ask AI')}</button>
			</div>
		</div>
		<div id="re-ai-answer" class="mt-3 p-3 bg-light rounded" style="min-height:48px;white-space:pre-wrap;display:none;font-size:.9rem"></div>
	</div>`;
}

function ask_portfolio_ai(question, page) {
	const $answer = page.main.find('#re-ai-answer');
	$answer.show().html('<em>' + __('Thinking…') + '</em>');
	frappe.call({
		method: 'real_estate.ai.portfolio_query.ask_portfolio',
		args: { question },
		callback: r => {
			$answer.text(r.message || __('No answer returned.'));
		},
	});
}
