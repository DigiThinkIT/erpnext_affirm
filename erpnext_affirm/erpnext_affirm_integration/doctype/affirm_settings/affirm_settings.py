# -*- coding: utf-8 -*-
# Copyright (c) 2018, Neil Lasrado and contributors
# For license information, please see license.txt

"""
# Integrating Affirm

### 1. Validate Currency Support

Example:

	from frappe.integrations.utils import get_payment_gateway_controller

	controller = get_payment_gateway_controller("Affirm")
	controller().validate_transaction_currency(currency)

### 2. Redirect for payment

Example:

	payment_details = {
		"amount": 600,
		"title": "Payment for bill : 111",
		"description": "payment via cart",
		"reference_doctype": "Payment Request",
		"reference_docname": "PR0001",
		"payer_email": "NuranVerkleij@example.com",
		"payer_name": "Nuran Verkleij",
		"order_id": "111",
		"currency": "USD",
		"payment_gateway": "Affirm"
	}

	# redirect the user to this url
	url = controller().get_payment_url(**payment_details)


### 3. On Completion of Payment

Write a method for `on_payment_authorized` in the reference doctype

Example:

	def on_payment_authorized(payment_status):
		# your code to handle callback
"""

from __future__ import unicode_literals
import frappe
import requests

from frappe.model.document import Document
from frappe.utils import get_url, call_hook_method, cint, getdate
from frappe.integrations.utils import create_payment_gateway, create_request_log
from six.moves.urllib.parse import urlencode

from requests.auth import HTTPBasicAuth
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

class AffirmSettings(Document):
	service_name = "Affirm"

	def validate(self):
		create_payment_gateway("Affirm")
		call_hook_method('payment_gateway_enabled', gateway=self.service_name)

	def get_payment_url(self, **kwargs):
		return get_url("./integrations/affirm_checkout?{0}".format(urlencode(kwargs)))


	def is_available(self, context=None, is_backend=0):
		'''AWC Specific API contract'''

		# never available to backend
		return not is_backend

@frappe.whitelist(allow_guest=1)
def affirm_callback(checkout_token, reference_doctype, reference_docname):

	affirm_settings = get_api_config()
	redirect_url = "/integrations/payment-failed"

	authorization_response = requests.post(
		"{api_url}/charges".format(**affirm_settings),
		auth=HTTPBasicAuth(
			affirm_settings.get('public_api_key'),
			affirm_settings.get('private_api_key')),
		json={"checkout_token": checkout_token})

	affirm_data = authorization_response.json()

	if affirm_data:
		charge_id = affirm_data.get('id')

		# check if callback already happened
		if affirm_data.get("status_code") == 400 and affirm_data.get("code") == "checkout-token-used":
			charge_id = affirm_data.get('charge_id')
			redirect_url = '/integrations/payment-success'
		else:
			pr = frappe.get_doc(reference_doctype, reference_docname)

			order_doc = frappe.get_doc(pr.reference_doctype, affirm_data.get('order_id'))
			order_doc.affirm_id = charge_id
			order_doc.flags.ignore_permissions = 1
			order_doc.save()

			# on awc you can skip creating an actual payment request and just
			# submit the sales order with this flag
			pr.flags.skip_payment_request = True
			pr.on_payment_authorized("Authorized")

			frappe.db.commit()

			redirect_url = '/integrations/payment-success'

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = get_url(redirect_url)

def get_api_config():
	settings = frappe.get_doc("Affirm Settings", "Affirm Settings")
	values = dict(
		public_api_key = settings.public_api_key,
		private_api_key = settings.private_api_key
	)

	if settings.is_sandbox:
		values.update(dict(
			checkout_url = settings.sandbox_checkout_url,
			api_url = settings.sandbox_api_url
		))
	else:
		values.update(dict(
			checkout_url = settings.live_checkout_url,
			api_url = settings.live_api_url
		))

	return values

def build_checkout_data(**kwargs):

	full_name = kwargs.get("payer_name")

	# Dirty Hack
	# Affirm needs Full Name to have atleast 2 words
	if len(full_name.split()) == 1:
		full_name = full_name + " ."

	# Pick up reference doc from payment request.
	# This is usually the payment request it self.
	# On awc its the awc transction proxy to the request.
	ref_doc = frappe.get_doc(kwargs['reference_doctype'], kwargs['reference_docname'])

	# fetch the actual doctype use for this transaction. Could be Quotation, Sales Order or Invoice
	order_doc = frappe.get_doc(ref_doc.reference_doctype, kwargs["order_id"])

	items = []
	discounts = {}
	shipping_address = frappe.get_doc("Address", order_doc.shipping_address_name)

	# deduce shipping from taxes table
	shipping_fee = 0
	for tax in order_doc.taxes:
		if 'shipping ' in tax.description.lower():
			shipping_fee = tax.tax_amount

	for item in order_doc.items:
		items.append({
			"display_name": item.item_name,
			"sku": item.item_code,
			"unit_price": convert_to_cents(item.rate),
			"qty": item.qty,
			"item_image_url": get_url(item.get("image", "")),
			"item_url": get_url()
		})

	if order_doc.coupon_code:
		discounts[order_doc.coupon_code] = {
				"discount_amount": order_doc.discount_amount,
				"discount_display_name": order_doc.coupon_code
			}

	checkout_data = {
		"merchant": {
			"user_confirmation_url": get_url(
				(
					"/api/method/erpnext_affirm.erpnext_affirm_integration"
					".doctype.affirm_settings.affirm_settings.affirm_callback"
					"?reference_doctype={0}&reference_docname={1}"
				).format(ref_doc.doctype, ref_doc.name)
			),
			"user_cancel_url": get_url("/cart"),
			"user_confirmation_url_action": "GET",
			"name": "JH Audio"
		},
		"shipping": {
			"name": {
				"full": full_name
			},
			"address": {
				"line1": shipping_address.get("address_line1"),
				"line2": shipping_address.get("address_line2"),
				"city": shipping_address.get("city"),
				"state": shipping_address.get("state"),
				"zipcode": shipping_address.get("pincode"),
				"country": shipping_address.get("country")
			}
		},
		"items": items,
		"discounts": discounts,
		"order_id": order_doc.name,
		"shipping_amount": convert_to_cents(shipping_fee),
		"tax_amount": convert_to_cents(order_doc.total_taxes_and_charges - shipping_fee),
		"total": convert_to_cents(order_doc.grand_total)
	}
	create_request_log(checkout_data, "Host", "Affirm")
	return checkout_data

@frappe.whitelist()
def capture_payment(affirm_id, sales_order):
	affirm_settings = get_api_config()
	authorization_response = requests.post(
		"{0}/charges/{1}/capture".format(affirm_settings.get("api_url"), affirm_id),
		auth=HTTPBasicAuth(
			affirm_settings.get('public_api_key'),
			affirm_settings.get('private_api_key')),
		)
	if authorization_response.status_code==200:
		affirm_data = authorization_response.json()
		#make payment entry agianst Sales Order
		payment_entry = get_payment_entry(dt="Sales Order", dn=sales_order, bank_amount=affirm_data.get("amount"))
		payment_entry.reference_no = affirm_data.get("transaction_id")
		payment_entry.reference_date = getdate(affirm_data.get("created"))
		payment_entry.submit()
	else:
		frappe.throw("Something went wrong.")

def convert_to_cents(amount):
	return cint(amount * 100)
