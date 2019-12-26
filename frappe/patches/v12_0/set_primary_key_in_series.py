import frappe

def execute():
    #if current = 0, simply delete the key as it'll be recreated on first entry
    frappe.db.sql('delete from `tabSeries` where current = 0')
    duplicate_keys = frappe.db.sql('''
        SELECT name, max(current) as current
        from
            `tabSeries`
        group by
            name
        having count(name) > 1
    ''', as_dict=True)
    for row in duplicate_keys:
        frappe.db.sql('delete from `tabSeries` where name = %(key)s', {
            'key': row.name
        })
        if row.current:
            frappe.db.sql('insert into `tabSeries`(`name`, `current`) values (%(name)s, %(current)s)', row)
    frappe.db.commit()
    if frappe.conf.db_type == 'mariadb':
        frappe.db.sql('ALTER table `tabSeries` ADD PRIMARY KEY IF NOT EXISTS (name)')
    elif frappe.conf.db_type == 'mysql':
        key_count = frappe.db.sql('''SELECT COUNT(*) as key_count
            FROM information_schema.statistics
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'tabSeries' 
            AND INDEX_NAME = 'name'; ''', as_dict=True)
        for row in key_count:
            if row.key_count == 0:
                frappe.db.sql('ALTER table `tabSeries` ADD INDEX (name)')
