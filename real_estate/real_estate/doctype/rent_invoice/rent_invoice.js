frappe.ui.form.on('Rent Invoice', {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status !== 'Paid') {
			frm.add_custom_button(__('Record Payment'), () => {
				show_payment_dialog(frm);
			});
		}
		if (frm.doc.linked_sales_invoice) {
			frm.add_custom_button(__('View Sales Invoice'), () => {
				frappe.set_route('Form', 'Sales Invoice', frm.doc.linked_sales_invoice);
			}, __('View'));
		}
		frm.set_indicator_formatter('status', row => {
			const map = { Paid: 'green', Unpaid: 'orange', Overdue: 'red', 'Partially Paid': 'yellow' };
			return map[row.status] || 'gray';
		});
	},

	lease(frm) {
		if (frm.doc.lease) {
			frappe.db.get_value('Lease Agreement', frm.doc.lease,
				['tenant', 'monthly_rent'],
				r => {
					frm.set_value('tenant', r.tenant);
					frm.set_value('base_rent', r.monthly_rent);
				}
			);
		}
	},

	base_rent(frm) { calculate_totals(frm); },
	late_fee(frm) { calculate_totals(frm); },
	discount(frm) { calculate_totals(frm); },
	vat_percent(frm) { calculate_totals(frm); },
});

frappe.ui.form.on('Utility Charge', {
	current_reading(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.previous_reading !== undefined && row.current_reading !== undefined) {
			frappe.model.set_value(cdt, cdn, 'consumption', row.current_reading - row.previous_reading);
			frappe.model.set_value(cdt, cdn, 'amount', (row.current_reading - row.previous_reading) * (row.rate_per_unit || 0));
		}
		calculate_totals(frm);
	},
	rate_per_unit(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, 'amount', (row.consumption || 0) * row.rate_per_unit);
		calculate_totals(frm);
	},
	utility_charges_remove(frm) { calculate_totals(frm); },
});

function calculate_totals(frm) {
	const utility_total = (frm.doc.utility_charges || []).reduce((s, r) => s + (r.amount || 0), 0);
	const subtotal = (frm.doc.base_rent || 0) + utility_total + (frm.doc.late_fee || 0) - (frm.doc.discount || 0);
	const vat_amount = subtotal * (frm.doc.vat_percent || 0) / 100;
	frm.set_value('subtotal', subtotal);
	frm.set_value('vat_amount', vat_amount);
	frm.set_value('total_amount', subtotal + vat_amount);
}

function show_payment_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __('Record Payment'),
		fields: [
			{ fieldname: 'amount', fieldtype: 'Currency', label: __('Amount Paid'), reqd: 1, default: frm.doc.total_amount },
			{ fieldname: 'payment_method', fieldtype: 'Select', label: __('Payment Method'),
			  options: 'Bank Transfer\nCheque\nCash\nCredit Card\nOnline', reqd: 1 },
			{ fieldname: 'payment_date', fieldtype: 'Date', label: __('Payment Date'), default: frappe.datetime.nowdate() },
		],
		primary_action_label: __('Record'),
		primary_action(values) {
			frm.call('record_payment', values).then(r => {
				d.hide();
				frm.reload_doc();
				frappe.show_alert({ message: __('Payment recorded. Status: {0}', [r.message]), indicator: 'green' });
			});
		},
	});
	d.show();
}
