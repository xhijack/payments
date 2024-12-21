import frappe
from frappe.utils import now_datetime, add_days

def bulk_payment_expire():
    frappe.msgprint("Cron job run for update Bulk Payment to expired!")
    
    # Dapatkan semua dokumen Bulk Payment Request yang statusnya 'Initiated' dan lebih dari 1 hari
    one_day_ago = add_days(now_datetime(), -1)
    bulk_payments = frappe.get_all("Bulk Payment Request", filters={
        "status": "Initiated",
        "docstatus": ["!=", 2],  # Exclude cancelled documents
        "creation": ["<", one_day_ago]
    })

    # Enqueue pembatalan dokumen
    for payment in bulk_payments:
        frappe.enqueue(cancel_bulk_payment, payment_name=payment.name)

    frappe.msgprint(f"{len(bulk_payments)} Bulk Payment Requests have been enqueued for cancellation.")

def cancel_bulk_payment(payment_name):
    doc = frappe.get_doc("Bulk Payment Request", payment_name)
    # Batalkan dokumen Bulk Payment Request
    frappe.db.set_value("Bulk Payment Request", payment_name, "status", "Expired")
    frappe.db.commit()
