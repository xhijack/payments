import frappe
from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest

def custom_get_payment_url(self):
    if self.reference_doctype != "Fees":
        data = frappe.db.get_value(
            self.reference_doctype, self.reference_name, ["company", "customer_name"], as_dict=1
        )
    else:
        data = frappe.db.get_value(
            self.reference_doctype, self.reference_name, ["student_name"], as_dict=1
        )
        data.update({"company": frappe.defaults.get_defaults().company})

    controller = _get_payment_gateway_controller(self.payment_gateway)
    controller.validate_transaction_currency(self.currency)

    if hasattr(controller, "validate_minimum_transaction_amount"):
        controller.validate_minimum_transaction_amount(self.currency, self.grand_total)

    return controller.get_payment_url(
        **{
            "amount": flt(self.grand_total, self.precision("grand_total")),
            "title": data.company,
            "description": self.subject,
            "reference_doctype": "Order Payment Request",
            "reference_docname": self.name,
            "payer_email": self.email_to or frappe.session.user,
            "payer_name": data.customer_name,
            "order_id": self.name,
            "currency": self.currency,
        }
    )

# Monkey patch the original method
PaymentRequest.get_payment_url = custom_get_payment_url