import frappe
import requests
from frappe.utils import get_url
from requests.auth import HTTPBasicAuth
from erpnext.selling.doctype.quotation.quotation import _make_sales_order

def get_context(context):
	token = frappe.local.request
	token = token.args.get('checkout_token')
	affirm_settings = frappe.db.get_singles_dict("Affirm Settings")
	redirect_url = "/integrations/payment-failed"
	if token:
		authorization_response = requests.post("https://sandbox.affirm.com/api/v2/charges", auth=HTTPBasicAuth(affirm_settings.public_api_key, affirm_settings.private_api_key), json={"checkout_token": token})
		affirm_data = authorization_response.json()
		if affirm_data.get("status_code") == 200:
			frappe.db.set_value("Quotation", affirm_data.get('order_id'), "affirm_id", affirm_data.get('id'))
			frappe.db.commit()
			quotation = frappe.get_doc("Quotation", affirm_data.get('order_id'))
			quotation.flags.ignore_permissions = 1
			quotation.run_method("on_payment_authorized", "Authorized")
			quotation.submit()
			sales_order = frappe.get_doc(_make_sales_order(quotation.name, ignore_permissions=True))
			sales_order.flags.ignore_permissions = 1
			sales_order.save()
			sales_order.submit()
			redirect_url = '/integrations/payment-success'

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = get_url(redirect_url)
	raise frappe.Redirect