frappe.query_reports["Salesperson Item Opportunities"] = {
  filters: [
    { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", reqd: 1, default: frappe.defaults.get_user_default("Company") },
    { fieldname: "from_date", label: __("From Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.add_months(frappe.datetime.get_today(), -3) },
    { fieldname: "to_date", label: __("To Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
    { fieldname: "item_code", label: __("Item Code"), fieldtype: "Link", options: "Item", reqd: 1 },
    { fieldname: "territory", label: __("Territory"), fieldtype: "Link", options: "Territory" },
    { fieldname: "city", label: __("City"), fieldtype: "Data" },
    { fieldname: "state", label: __("State"), fieldtype: "Data" },
    { fieldname: "customer_group", label: __("Customer Group"), fieldtype: "Link", options: "Customer Group" },
  ],
};

