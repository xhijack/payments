import frappe
from erpnext.accounts.doctype.payment_request.payment_request import resend_payment_email as original_resend_payment_email # type: ignore

@frappe.whitelist(allow_guest=True)
def resend_payment_email(docname):
    result = original_resend_payment_email("Order Payment Request", docname)
    return result
