import frappe
from frappe.utils import now_datetime, add_days

def bulk_payment_expire():
    frappe.msgprint("Cron job run for update Bulk Payment to expired!")
    
    # Dapatkan semua dokumen Bulk Payment Request yang statusnya 'Initiated' dan lebih dari 1 hari
    one_day_ago = add_days(now_datetime(), -1)
    bulk_payments = frappe.get_all("Bulk Payment Request", filters={
        "status": "Initiated",
        "creation": ["<", one_day_ago]
    })

    # Update status ke 'Cancelled'
    for payment in bulk_payments:
        doc = frappe.get_doc("Bulk Payment Request", payment.name)
        doc.status = "Cancelled"
        doc.save()
        frappe.db.commit()

    frappe.msgprint(f"{len(bulk_payments)} Bulk Payment Requests have been updated to 'Cancelled'.")
    # Tambahkan logika lain yang ingin dijalankan di sini
