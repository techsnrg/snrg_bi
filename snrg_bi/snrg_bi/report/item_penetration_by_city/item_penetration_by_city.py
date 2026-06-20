import frappe
from frappe import _


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


def get_columns():
    return [
        {"label": _("State"), "fieldname": "state", "fieldtype": "Data", "width": 140},
        {"label": _("City"), "fieldname": "city", "fieldtype": "Data", "width": 140},
        {"label": _("Territory"), "fieldname": "territory", "fieldtype": "Link", "options": "Territory", "width": 140},
        {"label": _("Total Customers"), "fieldname": "total_customers", "fieldtype": "Int", "width": 130},
        {"label": _("Buying Customers"), "fieldname": "buying_customers", "fieldtype": "Int", "width": 140},
        {"label": _("Opportunity Customers"), "fieldname": "opportunity_customers", "fieldtype": "Int", "width": 160},
        {"label": _("Penetration %"), "fieldname": "penetration_percent", "fieldtype": "Percent", "width": 130},
        {"label": _("Qty Bought"), "fieldname": "qty_bought", "fieldtype": "Float", "width": 120},
        {"label": _("Sales Value"), "fieldname": "sales_value", "fieldtype": "Currency", "width": 130},
    ]


def get_data(filters):
    conditions, params = get_customer_conditions(filters)
    query = f"""
        SELECT
            COALESCE(c.custom_state, '') AS state,
            COALESCE(c.custom_city, '') AS city,
            c.territory,
            COUNT(c.name) AS total_customers,
            SUM(CASE WHEN COALESCE(item_sales.qty_bought, 0) > 0 THEN 1 ELSE 0 END) AS buying_customers,
            SUM(CASE WHEN COALESCE(item_sales.qty_bought, 0) = 0 THEN 1 ELSE 0 END) AS opportunity_customers,
            ROUND(
                SUM(CASE WHEN COALESCE(item_sales.qty_bought, 0) > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(c.name),
                2
            ) AS penetration_percent,
            SUM(COALESCE(item_sales.qty_bought, 0)) AS qty_bought,
            SUM(COALESCE(item_sales.sales_value, 0)) AS sales_value
        FROM `tabCustomer` c
        LEFT JOIN (
            SELECT
                si.customer,
                SUM(sii.qty) AS qty_bought,
                SUM(sii.base_net_amount) AS sales_value
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            WHERE
                si.docstatus = 1
                AND COALESCE(si.is_return, 0) = 0
                AND si.company = %(company)s
                AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND sii.item_code = %(item_code)s
            GROUP BY si.customer
        ) item_sales ON item_sales.customer = c.name
        WHERE {conditions}
        GROUP BY COALESCE(c.custom_state, ''), COALESCE(c.custom_city, ''), c.territory
        ORDER BY opportunity_customers DESC, total_customers DESC, state ASC, city ASC
    """
    return frappe.db.sql(query, params, as_dict=True)


def get_customer_conditions(filters):
    conditions = ["1 = 1"]
    params = {
        "company": filters.company,
        "from_date": filters.from_date,
        "to_date": filters.to_date,
        "item_code": filters.item_code,
    }
    if filters.get("active_customers_only"):
        conditions.append("COALESCE(c.disabled, 0) = 0")
    for field, column in (
        ("territory", "c.territory"),
        ("state", "c.custom_state"),
        ("customer_group", "c.customer_group"),
    ):
        if filters.get(field):
            conditions.append(f"{column} = %({field})s")
            params[field] = filters.get(field)
    return " AND ".join(conditions), params


def get_summary(data):
    total_customers = sum(row.get("total_customers") or 0 for row in data)
    buying_customers = sum(row.get("buying_customers") or 0 for row in data)
    opportunities = sum(row.get("opportunity_customers") or 0 for row in data)
    penetration = (buying_customers * 100 / total_customers) if total_customers else 0
    return [
        {"label": _("Cities"), "value": len(data), "indicator": "Blue", "datatype": "Int"},
        {"label": _("Customers"), "value": total_customers, "indicator": "Blue", "datatype": "Int"},
        {"label": _("Buying Customers"), "value": buying_customers, "indicator": "Green", "datatype": "Int"},
        {"label": _("Opportunities"), "value": opportunities, "indicator": "Orange", "datatype": "Int"},
        {"label": _("Penetration %"), "value": penetration, "indicator": "Green", "datatype": "Percent"},
    ]

