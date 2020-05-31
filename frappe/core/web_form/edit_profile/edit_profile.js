frappe.ready(function() {
	// bind events here
	if (!window.location.href.includes('name')){
		window.location.href = '/update-profile?name=' + frappe.session.user;
	}
})