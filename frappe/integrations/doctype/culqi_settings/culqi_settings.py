# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.integrations.utils import create_payment_gateway, make_get_request, make_post_request, create_request_log
from frappe.utils import call_hook_method, get_url
from frappe import _

import json
import requests
from six.moves.urllib.parse import urlencode

class CulqiSettings(Document):
	supported_currencies = ["USD", "PEN"]

	def validate(self):
		create_payment_gateway("Culqi")
		call_hook_method('payment_gateway_enabled', gateway="Culqi")
		if not self.flags.ignore_mandatory:
			self.validate_culqi_credentails() 

	def get_culqi_headers_and_url(self, key_type="public"):
		header = {
			"Content-type": "application/json",
			"Authorization": "Bearer " + (self.api_key if key_type == "public" else self.get_password(fieldname="api_secret", raise_exception=False))
		}
		api_url = "https://secure.culqi.com/v2/" if key_type == "public" else "https://api.culqi.com/v2/"
		return header, api_url

	def validate_culqi_credentails(self):
		content = {
			"card_number": "4111111111111111",
			"cvv": "123",
			"expiration_month": "09",
			"expiration_year": "2020",
			"email": "richard@piedpiper.com"
		}
		try:
			pk_headers, api_url = self.get_culqi_headers_and_url()
			pk_response = make_post_request(api_url + "tokens", headers=pk_headers, data=json.dumps(content))
			if pk_response["object"] != "token":
				raise Exception
			sk_headers, api_url = self.get_culqi_headers_and_url(key_type="private")
			sk_response = make_get_request(api_url + "tokens", headers=sk_headers)
			if not sk_response["data"]:
				raise Exception
		except Exception:
			frappe.throw(_("Invalid payment gateway credentials"))
	
	def get_payment_settings(self, **kwargs):
		if kwargs['reference_docname']:
			frappe.cache().hset('payment_request', frappe.session.sid, kwargs)
		return frappe._dict({
			"store_name": self.store_name,
			"store_description": self.store_description,
			"currency": kwargs["currency"],
			"public_key": self.api_key
		})

	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(_("Please select another payment method. Culqi does not support transactions in currency '{0}'").format(currency))

@frappe.whitelist(allow_guest=True, xss_safe=True)
def get_express_checkout_details(**args):
	args = frappe._dict(args)
	custom_redirect_to = None
	try:
		doc = frappe.get_doc("Culqi Settings")
		pr_info = frappe.cache().hget("payment_request", frappe.session.sid)
		headers, url = doc.get_culqi_headers_and_url(key_type="private")

		charge_data = {
			"amount": int(args['amount']),
			"capture": False,
			"currency_code": args['currency_code'],
			"description": pr_info['description'],
			"email": args['email'],
			"installments": 0,
			"source_id": args['source_id'],
			"metadata": {
				"order_id": pr_info['order_id'],
				"payer_name": pr_info['payer_name']
			} 
		}

		response = requests.post(url + "charges", headers=headers, data=json.dumps(charge_data))
		data = json.loads(response.content)
		id = data.get("charge_id")  or data.get("id")
		create_request_log(pr_info, "Remote", "Culqi", id)

		if data.get('outcome'):
			if data.get('outcome').get('type') == 'venta_exitosa':
				doc = frappe.get_doc("Integration Request", id)
				update_integration_request_status(id, {
						"reference_code": data.get("reference_code")
					}, "Completed", doc=doc)
				if pr_info.get("reference_doctype") and pr_info.get("reference_docname"):
					custom_redirect_to = frappe.get_doc(pr_info.get("reference_doctype"),
						pr_info.get("reference_docname")).run_method("on_payment_authorized", "Completed")
					frappe.db.commit()
					redirect_url = '/integrations/payment-success?doctype={0}&docname={1}'.format(pr_info.get("reference_doctype"), pr_info.get("reference_docname"))
					redirect_url += '&' + urlencode({'redirect_to': custom_redirect_to})
		else:
			redirect_url = "/integrations/payment-failed" + '?' + urlencode({'redirect_to': '/orders'}) + '&' + urlencode({'redirect_message': data.get('user_message')})
				
		return redirect_url

	except Exception:
		frappe.log_error(frappe.get_traceback())

def update_integration_request_status(token, data, status, error=False, doc=None):
	if not doc:
		doc = frappe.get_doc("Integration Request", token)

	doc.update_status(data, status)