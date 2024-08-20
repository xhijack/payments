import frappe
from frappe.utils import nowdate
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from frappe.auth import LoginManager


@frappe.whitelist(allow_guest=True)
@frappe.whitelist()
def accept_payment(**data):
    """
    headers: X-CALLBACK-TOKEN
    data: {
        "id": "65f675eec32d920fd76d8034",
        "amount": 500000,
        "status": "PAID",
        "created": "2024-03-17T04:47:43.048Z",
        "is_high": false,
        "paid_at": "2024-03-17T04:48:32.000Z",
        "updated": "2024-03-17T04:48:33.041Z",
        "user_id": "65e0a60d213e0478ced4bb3e",
        "currency": "IDR",
        "bank_code": "MANDIRI",
        "payment_id": "46913fa1-3351-47c2-aa55-3b0fde81ee36",
        "description": "Invoice Demo #123",
        "external_id": "invoice-1231241",
        "paid_amount": 500000,
        "payer_email": "ramdani@sopwer.net",
        "merchant_name": "Sopwer",
        "payment_method": "BANK_TRANSFER",
        "payment_channel": "MANDIRI",
        "payment_destination": "8860827838227"
    }
    """
    login_manager = LoginManager()
    login_manager.authenticate("system@sopwer.net","SystemWebhook2024")
    login_manager.post_login()

    data = frappe.parse_json(data)
    payment_log = frappe.get_list("Xendit Payment Log", filters={"document": data['external_id']}, fields=["name"])
    if payment_log:
        xpl = frappe.get_doc("Xendit Payment Log", payment_log[0].name)
        token_verify = frappe.db.get_value("Xendit Settings", xpl.xendit_account, "token_verify")
        if frappe.request.headers.get('X-CALLBACK-TOKEN') == token_verify:
            pr = frappe.get_doc(xpl.doc_type, xpl.document)
            if pr.payment_request_type == "Inward":
                 payment_type = "Receive"
            else:
                payment_type = "Pay"
            pe = get_payment_entry(dt=pr.reference_doctype, dn=pr.reference_name, party_type=pr.party_type, payment_type=payment_type)

            # Ubah status payment entry menjadi "paid"
            pe.reference_no = data['external_id']
            pe.reference_date = data['paid_at'][:10]
            pe.save(ignore_permissions=True)
            pe.submit()
            # Update Xendit Payment Log
            frappe.db.set_value("Xendit Payment Log", payment_log[0].name, "status", data['status'])
            frappe.db.set_value("Xendit Payment Log", payment_log[0].name, "callback_payload", frappe.as_json(data))
            frappe.db.commit()

            return "Payment entry updated successfully"
        else:
            frappe.log_error("Request Payment {0} Is Invalid".format(data['id']))
            return "Request Payment {0} Is Invalid".format(data['id'])

    else:
        frappe.log_error("Error Payment {0} Log Not Found".format(data['id']))
        return "Payment log not found"
    

def get_combined_payment_entry(bulk_payment_request):
	bpr = frappe.get_doc('Bulk Payment Request', bulk_payment_request)
	si_names = [invoice.sales_invoice for invoice in bpr.invoices]
	if not isinstance(si_names, list):
		si_names = [si_names]

	first_si = si_names[0]
	pe = get_payment_entry('Sales Invoice', first_si)
	pe.reference_no = bpr.name
	pe.reference_date = nowdate()
	pe.mode_of_payment = bpr.mode_of_payment
	pe.flags.ignore_mandatory = True
	pe.references = []
	for si in bpr.invoices:
		si_doc = frappe.get_doc('Sales Invoice', si.sales_invoice)
		if not pe.references:
			pe.references = []
		pe.append('references', {
			'reference_doctype': 'Sales Invoice',
			'reference_name': si.sales_invoice,
			'total_amount': float(si_doc.grand_total),
			'outstanding_amount': float(si_doc.outstanding_amount),
			'allocated_amount': float(si.amount),
			'payment_term': si.payment_term
		})
		pe.paid_amount += float(si_doc.outstanding_amount)
		pe.received_amount += float(si_doc.outstanding_amount)

	pe.set_missing_values()
	pe.save()
	pe.submit()

	frappe.db.set_value('Bulk Payment Request', bpr.name, 'status', 'Paid')

	return pe.name

def create_multiple_invoice(bulk_payment_request):
    bpr = frappe.get_doc('Bulk Payment Request', bulk_payment_request)
    for si in bpr.invoices:
        si_doc = frappe.get_doc('Sales Invoice', si.sales_invoice)
        pe = get_payment_entry('Sales Invoice', si.sales_invoice)
        pe.reference_no = bpr.name
        pe.reference_date = nowdate()
        pe.mode_of_payment = bpr.mode_of_payment
        pe.flags.ignore_mandatory = True
        pe.references = []
        pe.append('references', {
            'reference_doctype': 'Sales Invoice',
            'reference_name': si.sales_invoice,
            'total_amount': float(si_doc.grand_total),
            'outstanding_amount': float(si_doc.outstanding_amount),
            'allocated_amount': float(si.amount),
            'payment_term': si.payment_term
        })
        pe.paid_amount = float(si.amount)
        pe.received_amount = float(si.amount)

        pe.set_missing_values()
        pe.save()
        pe.submit()
                            


@frappe.whitelist(allow_guest=True)
def accept_payment_multi_invoice(**data):
    """
    headers: X-CALLBACK-TOKEN
    data: {
        "id": "65f675eec32d920fd76d8034",
        "amount": 500000,
        "status": "PAID",
        "created": "2024-03-17T04:47:43.048Z",
        "is_high": false,
        "paid_at": "2024-03-17T04:48:32.000Z",
        "updated": "2024-03-17T04:48:33.041Z",
        "user_id": "65e0a60d213e0478ced4bb3e",
        "currency": "IDR",
        "bank_code": "MANDIRI",
        "payment_id": "46913fa1-3351-47c2-aa55-3b0fde81ee36",
        "description": "Invoice Demo #123",
        "external_id": "invoice-1231241",
        "paid_amount": 500000,
        "payer_email": "ramdani@sopwer.net",
        "merchant_name": "Sopwer",
        "payment_method": "BANK_TRANSFER",
        "payment_channel": "MANDIRI",
        "payment_destination": "8860827838227"
    }
    """

    data = frappe.parse_json(data)
    payment_log = frappe.get_list("Xendit Payment Log", filters={"document": data['external_id']}, fields=["name"])
    if payment_log:
        xpl = frappe.get_doc("Xendit Payment Log", payment_log[0].name)
        token_verify = frappe.db.get_value("Xendit Settings", xpl.xendit_account, "token_verify")
        if frappe.request.headers.get('X-Callback-Token') == token_verify:
            
            create_multiple_invoice(xpl.document)

            # Update Xendit Payment Log
            frappe.db.set_value("Xendit Payment Log", payment_log[0].name, "status", data['status'])
            frappe.db.set_value("Xendit Payment Log", payment_log[0].name, "callback_payload", frappe.as_json(data))
            frappe.db.set_value('Bulk Payment Request', xpl.document, 'status', 'Paid')

            frappe.db.commit()

            return "Payment entry updated successfully"
        else:
            frappe.log_error("Request Payment {0} Is Invalid".format(data['id']))
            return "Request Payment {0} Is Invalid".format(data['id'])

    else:
        frappe.log_error("Error Payment {0} Log Not Found".format(data['id']))
        return "Payment log not found"