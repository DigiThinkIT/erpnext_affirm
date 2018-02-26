# -*- coding: utf-8 -*-
# Copyright (c) 2018, Neil Lasrado and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import call_hook_method
from frappe.integrations.utils import create_payment_gateway
class AffirmSettings(Document):
	def validate(self):
		create_payment_gateway("Affirm")
		call_hook_method('payment_gateway_enabled', gateway="Affirm")

	def get_payment_url(self, **kwargs):
		return "/affirm"