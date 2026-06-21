frappe.query_reports["Customer Basket Gap"] = {
  filters: [
    { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", reqd: 1, default: frappe.defaults.get_user_default("Company") },
    { fieldname: "from_date", label: __("From Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.add_months(frappe.datetime.get_today(), -6) },
    { fieldname: "to_date", label: __("To Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
    { fieldname: "has_target_type", label: __("Buys Target Type"), fieldtype: "Select", options: "Item\nItem Group", default: "Item", reqd: 1 },
    { fieldname: "has_item_code", label: __("Buys Item"), fieldtype: "Link", options: "Item", depends_on: "eval:doc.has_target_type == 'Item'", mandatory_depends_on: "eval:doc.has_target_type == 'Item'" },
    { fieldname: "has_item_group", label: __("Buys Item Group"), fieldtype: "Link", options: "Item Group", depends_on: "eval:doc.has_target_type == 'Item Group'", mandatory_depends_on: "eval:doc.has_target_type == 'Item Group'" },
    { fieldname: "missing_target_type", label: __("Missing Target Type"), fieldtype: "Select", options: "Item\nItem Group", default: "Item", reqd: 1 },
    { fieldname: "missing_item_code", label: __("Does Not Buy Item"), fieldtype: "Link", options: "Item", depends_on: "eval:doc.missing_target_type == 'Item'", mandatory_depends_on: "eval:doc.missing_target_type == 'Item'" },
    { fieldname: "missing_item_group", label: __("Does Not Buy Item Group"), fieldtype: "Link", options: "Item Group", depends_on: "eval:doc.missing_target_type == 'Item Group'", mandatory_depends_on: "eval:doc.missing_target_type == 'Item Group'" },
    { fieldname: "territory", label: __("Territory"), fieldtype: "Link", options: "Territory" },
    { fieldname: "city", label: __("City"), fieldtype: "Data" },
    { fieldname: "state", label: __("State"), fieldtype: "Data" },
    { fieldname: "customer_group", label: __("Customer Group"), fieldtype: "Link", options: "Customer Group" },
    { fieldname: "sales_person", label: __("Sales Person"), fieldtype: "Link", options: "Sales Person" },
    { fieldname: "active_customers_only", label: __("Active Customers Only"), fieldtype: "Check", default: 1 },
  ],
};
