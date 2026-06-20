frappe.query_reports["Customer Basket Gap"] = {
  filters: [
    { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", reqd: 1, default: frappe.defaults.get_user_default("Company") },
    { fieldname: "from_date", label: __("From Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.add_months(frappe.datetime.get_today(), -6) },
    { fieldname: "to_date", label: __("To Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
    { fieldname: "has_item_code", label: __("Buys Item"), fieldtype: "Link", options: "Item", reqd: 1 },
    { fieldname: "missing_item_code", label: __("Does Not Buy Item"), fieldtype: "Link", options: "Item", reqd: 1 },
    { fieldname: "territory", label: __("Territory"), fieldtype: "Link", options: "Territory" },
    { fieldname: "city", label: __("City"), fieldtype: "Data" },
    { fieldname: "state", label: __("State"), fieldtype: "Data" },
    { fieldname: "customer_group", label: __("Customer Group"), fieldtype: "Link", options: "Customer Group" },
    { fieldname: "sales_person", label: __("Sales Person"), fieldtype: "Link", options: "Sales Person" },
    { fieldname: "active_customers_only", label: __("Active Customers Only"), fieldtype: "Check", default: 1 },
  ],
};

