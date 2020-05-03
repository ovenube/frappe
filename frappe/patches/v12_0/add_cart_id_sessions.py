from __future__ import unicode_literals
import frappe

def execute():
	if "device" not in frappe.db.get_table_columns("Sessions"):
		frappe.db.sql("alter table tabSessions add column `cart_id` varchar(255) default NULL")
