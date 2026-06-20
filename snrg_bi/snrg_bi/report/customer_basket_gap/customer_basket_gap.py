import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)
    data = get_data(filters)
    return get_columns(), data, None, None, get_summary(data)


def validate_filters(filters):
    required = ["company", "from_date", "to_date", "has_item_code", "missing_item_code"]
    missing = [field for field in required if not filters.get(field)]
    if missing:
        frappe.throw(_("Missing required filters: {0}").format(", ".join(missing)))
    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date cannot be after To Date"))
    if filters.has_item_code == filters.missing_item_code:
        frappe.throw(_("Buys Item and Does Not Buy Item must be different"))


def get_columns():
    return [
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 140},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 220},
        {"label": _("Territory"), "fieldname": "territory", "fieldtype": "Link", "options": "Territory", "width": 130},
        {"label": _("City"), "fieldname": "city", "fieldtype": "Data", "width": 120},
        {"label": _("State"), "fieldname": "state", "fieldtype": "Data", "width": 130},
        {"label": _("Customer Group"), "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 150},
        {"label": _("Sales Person"), "fieldname": "sales_person", "fieldtype": "Data", "width": 180},
        {"label": _("Buys Item Qty"), "fieldname": "has_item_qty", "fieldtype": "Float", "width": 120},
        {"label": _("Buys Item Value"), "fieldname": "has_item_value", "fieldtype": "Currency", "width": 130},
        {"label": _("Missing Item Qty"), "fieldname": "missing_item_qty", "fieldtype": "Float", "width": 130},
        {"label": _("Last Bought Base Item"), "fieldname": "last_has_item_date", "fieldtype": "Date", "width": 150},
        {"label": _("Opportunity"), "fieldname": "opportunity", "fieldtype": "Data", "width": 120},
    ]


def get_data(filters):
    conditions, params = get_customer_conditions(filters)
    query = f"""
        SELECT
            c.name AS customer,
            c.customer_name,
            c.territory,
            c.custom_city AS city,
            c.custom_state AS state,
            c.customer_group,
            sales_team.sales_person,
            has_sales.qty AS has_item_qty,
            has_sales.value AS has_item_value,
            COALESCE(missing_sales.qty, 0) AS missing_item_qty,
            has_sales.last_purchase_date AS last_has_item_date,
            'Cross-sell' AS opportunity
        FROM `tabCustomer` c
        INNER JOIN (
            SELECT
                si.customer,
                SUM(sii.qty) AS qty,
                SUM(sii.base_net_amount) AS value,
                MAX(si.posting_date) AS last_purchase_date
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            WHERE
                si.docstatus = 1
                AND COALESCE(si.is_return, 0) = 0
                AND si.company = %(company)s
                AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND sii.item_code = %(has_item_code)s
            GROUP BY si.customer
        ) has_sales ON has_sales.customer = c.name
        LEFT JOIN (
            SELECT
                si.customer,
                SUM(sii.qty) AS qty
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            WHERE
                si.docstatus = 1
                AND COALESCE(si.is_return, 0) = 0
                AND si.company = %(company)s
                AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND sii.item_code = %(missing_item_code)s
            GROUP BY si.customer
        ) missing_sales ON missing_sales.customer = c.name
        LEFT JOIN (
            SELECT parent, GROUP_CONCAT(DISTINCT sales_person ORDER BY sales_person SEPARATOR ', ') AS sales_person
            FROM `tabSales Team`
            WHERE parenttype = 'Customer'
            GROUP BY parent
        ) sales_team ON sales_team.parent = c.name
        WHERE {conditions}
            AND COALESCE(missing_sales.qty, 0) = 0
        ORDER BY has_sales.value DESC, c.customer_name ASC
    """
    return frappe.db.sql(query, params, as_dict=True)


def get_customer_conditions(filters):
    conditions = ["1 = 1"]
    params = {
        "company": filters.company,
        "from_date": filters.from_date,
        "to_date": filters.to_date,
        "has_item_code": filters.has_item_code,
        "missing_item_code": filters.missing_item_code,
    }
    if filters.get("active_customers_only"):
        conditions.append("COALESCE(c.disabled, 0) = 0")
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
        {"label": _("Opportunities"), "value": len(data), "indicator": "Orange", "datatype": "Int"},
        {"label": _("Base Item Qty"), "value": sum(row.get("has_item_qty") or 0 for row in data), "indicator": "Blue", "datatype": "Float"},
        {"label": _("Base Item Value"), "value": sum(row.get("has_item_value") or 0 for row in data), "indicator": "Green", "datatype": "Currency"},
    ]

