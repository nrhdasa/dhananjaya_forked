# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt
from dhananjaya.dhananjaya.utils import get_best_contact_address, get_formatted_address
import frappe
from frappe.model.document import Document
from frappe.utils import random_string
from frappe.utils.data import money_in_words


class DhananjayaSettings(Document):
    pass


@frappe.whitelist()
def get_print_donation(dr):
    dr_doc = frappe.get_doc("Donation Receipt", dr)

    settings_doc = frappe.get_cached_doc("Dhananjaya Settings")
    company_detail = None
    for d in settings_doc.company_details:
        if d.company == dr_doc.company:
            company_detail = d

    sevak_name = None

    if dr_doc.patron:
        sevak_name = frappe.db.get_value("Patron", dr_doc.patron, "full_name") + "(P)"
    elif dr_doc.sevak_name:
        sevak_name = dr_doc.sevak_name

    if dr_doc.donor:
        donor_doc = frappe.get_doc("Donor", dr_doc.donor)

        address, contact, email = get_best_contact_address(donor_doc.name)

        dr_data = {
            "full_name": donor_doc.full_name,
            "pan_no": donor_doc.pan_no,
            "aadhar_no": donor_doc.aadhar_no,
            # "address": get_formatted_address(address),
            "address": dr_doc.address,
            "contact": "" if dr_doc.contact is None else dr_doc.contact,
            "email": "" if email is None else email,
            "money_in_words": money_in_words(dr_doc.amount, main_currency="Rupees"),
        }
        if sevak_name:
            dr_data.update({"sevak_name": sevak_name})
    else:
        donor_creation_request_doc = frappe.get_doc(
            "Donor Creation Request", dr_doc.donor_creation_request
        )

        address_values = [
            donor_creation_request_doc.address_line_1,
            donor_creation_request_doc.address_line_2,
            donor_creation_request_doc.city,
            donor_creation_request_doc.state,
            donor_creation_request_doc.pin_code,
        ]
        non_null_values = [
            i.strip(",") for i in address_values if (i is not None and len(i) > 0)
        ]
        address = ",".join(non_null_values)

        dr_data = {
            "full_name": donor_creation_request_doc.full_name,
            "pan_no": donor_creation_request_doc.pan_number,
            "aadhar_no": donor_creation_request_doc.aadhar_number,
            "address": address,
            "contact": donor_creation_request_doc.contact_number,
            "email": None,
            "money_in_words": money_in_words(dr_doc.amount, main_currency="Rupees"),
        }

    ### Get Reference Number also if Realised.
    dr_data.update({"reference_number": ""})
    if dr_doc.bank_transaction:
        tx_doc = frappe.get_doc("Bank Transaction", dr_doc.bank_transaction)
        dr_data.update({"reference_number": tx_doc.description})

    return company_detail.as_dict(), dr_data


@frappe.whitelist(methods=["POST"])
def refresh_versions():
    for dv in frappe.get_all("Dhananjaya Notifier"):
        frappe.db.set_value(
            "Dhananjaya Notifier", dv["name"], "version", random_string(6)
        )
    return
