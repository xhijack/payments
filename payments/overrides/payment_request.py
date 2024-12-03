import frappe

@frappe.whitelist(allow_guest=True)
def resend_payment_email(docname):
        # Mengambil dokumen "Order Payment Request" berdasarkan docname
    order_payment_request = frappe.get_doc("Order Payment Request", docname)
    # Memanggil metode send_email pada dokumen yang diambil
    return order_payment_request.send_email()
