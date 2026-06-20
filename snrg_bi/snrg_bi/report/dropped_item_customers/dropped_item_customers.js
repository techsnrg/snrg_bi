frappe.query_reports["Dropped Item Customers"] = {
  filters: [
    { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", reqd: 1, default: frappe.defaults.get_user_default("Company") },
    { fieldname: "from_date", label: __("No Purchase From"), fieldtype: "Date", reqd: 1, default: frappe.datetime.add_months(frappe.datetime.get_today(), -3) },
    { fieldname: "to_date", label: __("No Purchase To"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
    { fieldname: "lookback_months", label: __("Prior Lookback Months"), fieldtype: "Int", default: 12 },
    { fieldname: "item_code", label: __("Item Code"), fieldtype: "Link", options: "Item", reqd: 1 },
    { fieldname: "territory", label: __("Territory"), fieldtype: "Link", options: "Territory" },
    { fieldname: "city", label: __("City"), fieldtype: "Data" },
    { fieldname: "state", label: __("State"), fieldtype: "Data" },
    { fieldname: "customer_group", label: __("Customer Group"), fieldtype: "Link", options: "Customer Group" },
    { fieldname: "sales_person", label: __("Sales Person"), fieldtype: "Link", options: "Sales Person" },
  ],
};

