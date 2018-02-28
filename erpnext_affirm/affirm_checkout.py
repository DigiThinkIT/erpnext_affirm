# -*- coding: utf-8 -*-
# Copyright (c) 2018, Neil Lasrado and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import get_url
from frappe.integrations.utils import create_request_log
from awesome_cart.compat.customer import get_current_customer
from awesome_cart.session import get_awc_session
from awesome_cart.awc import get_user_quotation

@frappe.whitelist()
def get_checkout_data():
	public_api_key = frappe.db.get_single_value("Affirm Settings", "public_api_key")
	script_url = frappe.db.get_single_value("Affirm Settings", "script_url")

	customer = get_current_customer()
	full_name = customer.customer_name

	# Dirty Hack
	# Affirm needs Full Name to have atleast 2 words
	if len(full_name.split()) == 1:
		full_name = full_name + " ."

	awc_session = get_awc_session()
	cart_info = get_user_quotation(awc_session)
	quotation = cart_info.get('doc')

	items = []
	shipping_address = awc_session.get("shipping_address")
	shipping_fee = awc_session.get("shipping_method").get("fee")

	for item in quotation.items:
		items.append({
			"display_name": item.item_name,
			"sku": item.item_code,
			"unit_price": convert_to_cents(item.rate),
			"qty": item.qty,
			"item_image_url": get_url() + item.get("image", ""),
			"item_url": get_url()
		})

	checkout_data = {
		"merchant": {
			"user_confirmation_url": get_url() + "/affirm_success",
			"user_cancel_url": get_url() + "/cart",
			"user_confirmation_url_action": "POST",
			"name": "JH Audio"
		},
		"shipping": {
			"name": {
				"full": full_name
			},
			"address": {
				"line1": shipping_address.get("address_1"),
				"line2": shipping_address.get("address_2"),
				"city": shipping_address.get("city"),
				"state": shipping_address.get("state"),
				"zipcode": shipping_address.get("pincode"),
				"country": shipping_address.get("country")
			}
		},
		"items": items,
		"order_id": quotation.name,
		"shipping_amount": convert_to_cents(shipping_fee),
		"tax_amount": convert_to_cents(quotation.total_taxes_and_charges - shipping_fee),
		"total": convert_to_cents(quotation.grand_total),
		"reference_doctype": "Quotation",
		"reference_docname": quotation.name
	}

	create_request_log(checkout_data, "Host", "Affirm")
	return {
		"public_api_key": public_api_key,
		"script_url": script_url,
		"checkout_data": checkout_data
	}

def convert_to_cents(amount):
	return amount * 100