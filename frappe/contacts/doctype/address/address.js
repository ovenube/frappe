// Copyright (c) 2016, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Address", {
	refresh: function(frm, cdt, cdn) {
		if(frm.doc.country == "Peru"){
			frappe.db.get_list("Departamento", {fields: ["department_name"], filters: {country: frm.doc.country}, limit:1000}).then((result) => {
				var departments = []
				result.forEach(department => {
					departments.push(department["department_name"]);
				})
				frappe.meta.get_docfield(cdt, 'departamento', frm.doc.name).options = departments.reverse();
				frm.refresh_field("departamento");
				if (frm.doc.departamento){
					frappe.call({
						method: "frappe.contacts.doctype.address.address.get_provinces",
						args: {
							country: frm.doc.country,
							department: frm.doc.departamento
						},
						callback: function(r, rt){
							if(r.message){
								frappe.meta.get_docfield(cdt, 'provincia', frm.doc.name).options = r.message;
								frm.refresh_field("provincia");
							}
						}
					});
				}
				if (frm.doc.provincia){
					frappe.call({
						method: "frappe.contacts.doctype.address.address.get_districts",
						args: {
							country: frm.doc.country,
							department: frm.doc.departamento,
							province: frm.doc.provincia
						},
						callback: function(r, rt){
							if(r.message){
								frappe.meta.get_docfield(cdt, 'distrito', frm.doc.name).options = r.message;
								frm.refresh_field("distrito");
							}
						}
					});
				}
			})
			
		}
		if(frm.doc.__islocal) {
			const last_doc = frappe.contacts.get_last_doc(frm);
			if(frappe.dynamic_link && frappe.dynamic_link.doc
					&& frappe.dynamic_link.doc.name == last_doc.docname) {
				frm.set_value('links', '');
				frm.add_child('links', {
					link_doctype: frappe.dynamic_link.doctype,
					link_name: frappe.dynamic_link.doc[frappe.dynamic_link.fieldname]
				});
			}
		}
		frm.set_query('link_doctype', "links", function() {
			return {
				query: "frappe.contacts.address_and_contact.filter_dynamic_link_doctypes",
				filters: {
					fieldtype: "HTML",
					fieldname: "address_html",
				}
			}
		});
		frm.refresh_field("links");

		if (frm.doc.links) {
			for (let i in frm.doc.links) {
				let link = frm.doc.links[i];
				frm.add_custom_button(__("{0}: {1}", [__(link.link_doctype), __(link.link_name)]), function() {
					frappe.set_route("Form", link.link_doctype, link.link_name);
				}, __("Links"));
			}
		}
	},
	country: function(frm, cdt, cdn){
		if (frm.doc.country == "Peru"){
			frappe.call({
				method: "frappe.contacts.doctype.address.address.get_departments",
				args: {
					country: frm.doc.country
				},
				callback: function(r, rt){
					if(r.message){
						frappe.meta.get_docfield(cdt, 'departamento', frm.doc.name).options = r.message.reverse();
						frappe.meta.get_docfield(cdt, 'provincia', frm.doc.name).options = [];
						frappe.meta.get_docfield(cdt, 'distrito', frm.doc.name).options = [];
						frm.set_value("ubigeo", "");
						frm.refresh_field("departamento");
						frm.refresh_field("provincia");
						frm.refresh_field("distrito");
					}
				}
			})
		}
	},
	departamento: function(frm, cdt, cdn){
		if (frm.doc.country == "Peru"){
			frappe.call({
				method: "frappe.contacts.doctype.address.address.get_provinces",
				args: {
					country: frm.doc.country,
					department: frm.doc.departamento
				},
				callback: function(r, rt){
					if(r.message){
						frappe.meta.get_docfield(cdt, 'provincia', frm.doc.name).options = r.message;
						frappe.meta.get_docfield(cdt, 'distrito', frm.doc.name).options = [];
						frm.set_value("ubigeo", "");
						frm.refresh_field("provincia");
						frm.refresh_field("distrito");
					}
				}
			})
		}
	},
	provincia: function(frm, cdt, cdn){
		if (frm.doc.country == "Peru"){
			frappe.call({
				method: "frappe.contacts.doctype.address.address.get_districts",
				args: {
					country: frm.doc.country,
					department: frm.doc.departamento,
					province: frm.doc.provincia
				},
				callback: function(r, rt){
					if(r.message){
						frappe.meta.get_docfield(cdt, 'distrito', frm.doc.name).options = r.message;
						frm.set_value("ubigeo", "");
						frm.refresh_field("distrito");
					}
				}
			})
		}		
	},
	distrito: function(frm, cdt, cdn){
		if (frm.doc.country == "Peru"){
			frappe.call({
				method: "frappe.contacts.doctype.address.address.get_ubigeo",
				args: {
					country: frm.doc.country,
					department: frm.doc.departamento,
					province: frm.doc.provincia,
					district: frm.doc.distrito
				},
				callback: function(r, rt){
					if (r.message){
						frm.set_value("ubigeo", r.message);
					}
				}
			})
		}
	},
	validate: function(frm) {
		// clear linked customer / supplier / sales partner on saving...
		if(frm.doc.links) {
			frm.doc.links.forEach(function(d) {
				frappe.model.remove_from_locals(d.link_doctype, d.link_name);
			});
		}
	},
	after_save: function(frm) {
		frappe.run_serially([
			() => frappe.timeout(1),
			() => {
				const last_doc = frappe.contacts.get_last_doc(frm);
				if (frappe.dynamic_link && frappe.dynamic_link.doc && frappe.dynamic_link.doc.name == last_doc.docname) {
					for (let i in frm.doc.links) {
						let link = frm.doc.links[i];
						if (last_doc.doctype == link.link_doctype && last_doc.docname == link.link_name) {
							frappe.set_route('Form', last_doc.doctype, last_doc.docname);
						}
					}
				}
			}
		]);
	}
});
