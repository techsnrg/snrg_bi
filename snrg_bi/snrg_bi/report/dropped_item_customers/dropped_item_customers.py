import frappe
from frappe import _
from frappe.utils import add_months


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)
    data = get_data(filters)
    return get_columns(), data, None, None, get_summary(data)


def validate_filters(filters):
    required = ["company", "from_date", "to_date", "item_code"]
    missing = [field for field in required if not filters.get(field)]
    if missing:
        frappe.throw(_("Missing required filters: {0}").format(", ".join(missing)))
    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date cannot be after To Date"))
    if not filters.get("lookback_months"):
        filters.lookback_months = 12


def get_columns():
    return [
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 140},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 220},
        {"label": _("Territory"), "fieldname": "territory", "fieldtype": "Link", "options": "Territory", "width": 130},
        {"label": _("City"), "fieldname": "city", "fieldtype": "Data", "width": 120},
        {"label": _("State"), "fieldname": "state", "fieldtype": "Data", "width": 130},
        {"label": _("Customer Group"), "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 150},
        {"label": _("Sales Person"), "fieldname": "sales_person", "fieldtype": "Data", "width": 180},
        {"label": _("Prior Qty"), "fieldname": "prior_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Prior Value"), "fieldname": "prior_value", "fieldtype": "Currency", "width": 130},
        {"label": _("Last Purchase Date"), "fieldname": "last_purchase_date", "fieldtype": "Date", "width": 140},
        {"label": _("Days Since Last Purchase"), "fieldname": "days_since_last_purchase", "fieldtype": "Int", "width": 170},
    ]


def get_data(filters):
    lookback_from_date = add_months(filters.from_date, -int(filters.lookback_months))
    conditions, params = get_customer_conditions(filters)
    params["lookback_from_date"] = lookback_from_date

    query = f"""
        SELECT
            c.name AS customer,
            c.customer_name,
            c.territory,
            c.custom_city AS city,
            c.custom_state AS state,
            c.customer_group,
            sales_team.sales_person,
            prior_sales.prior_qty,
            prior_sales.prior_value,
            prior_sales.last_purchase_date,
            DATEDIFF(%(to_date)s, prior_sales.last_purchase_date) AS days_since_last_purchase
        FROM `tabCustomer` c
        INNER JOIN (
            SELECT
                si.customer,
                SUM(sii.qty) AS prior_qty,
                SUM(sii.base_net_amount) AS prior_value,
                MAX(si.posting_date) AS last_purchase_date
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            WHERE
                si.docstatus = 1
                AND COALESCE(si.is_return, 0) = 0
                AND si.company = %(company)s
                AND si.posting_date >= %(lookback_from_date)s
                AND si.posting_date < %(from_date)s
                AND sii.item_code = %(item_code)s
            GROUP BY si.customer
        ) prior_sales ON prior_sales.customer = c.name
        LEFT JOIN (
            SELECT si.customer, SUM(sii.qty) AS current_qty
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            WHERE
                si.docstatus = 1
                AND COALESCE(si.is_return, 0) = 0
                AND si.company = %(company)s
                AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND sii.item_code = %(item_code)s
            GROUP BY si.customer
        ) current_sales ON current_sales.customer = c.name
        LEFT JOIN (
            SELECT parent, GROUP_CONCAT(DISTINCT sales_person ORDER BY sales_person SEPARATOR ', ') AS sales_person
            FROM `tabSales Team`
            WHERE parenttype = 'Customer'
            GROUP BY parent
        ) sales_team ON sales_team.parent = c.name
        WHERE {conditions}
            AND COALESCE(current_sales.current_qty, 0) = 0
        ORDER BY prior_sales.prior_value DESC, prior_sales.last_purchase_date ASC
    """
    return frappe.db.sql(query, params, as_dict=True)


def get_customer_conditions(filters):
    conditions = ["COALESCE(c.disabled, 0) = 0"]
    params = {
        "company": filters.company,
        "from_date": filters.from_date,
        "to_date": filters.to_date,
        "item_code": filters.item_code,
    }
    for field, column in (
        ("territory", "c.territory"),
        ("city", "c.custom_city"),
        ("state", "c.custom_state"),
        ("customer_group", "c.customer_group"),
    ):
        if filters.get(field):
            conditions.append(f"{column} = %({field})s")
            params[field] = filters.get(field)
    if filters.get("sales_person"):
        conditions.append(
            """
            EXISTS (
                SELECT 1 FROM `tabSales Team` st
                WHERE st.parenttype = 'Customer'
                    AND st.parent = c.name
                    AND st.sales_person = %(sales_person)s
            )
            """
        )
        params["sales_person"] = filters.sales_person
    return " AND ".join(conditions), params


def get_summary(data):
    return [
        {"label": _("Dropped Customers"), "value": len(data), "indicator": "Red", "datatype": "Int"},
        {"label": _("Prior Qty"), "value": sum(row.get("prior_qty") or 0 for row in data), "indicator": "Blue", "datatype": "Float"},
        {"label": _("Prior Value"), "value": sum(row.get("prior_value") or 0 for row in data), "indicator": "Green", "datatype": "Currency"},
    ]

