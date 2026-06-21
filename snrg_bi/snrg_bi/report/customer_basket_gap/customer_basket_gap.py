import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)
    missing_target_message = get_missing_target_message(filters)
    if missing_target_message:
        return get_columns(), [], missing_target_message, None, []

    data = get_data(filters)
    return get_columns(), data, None, None, get_summary(data)


def validate_filters(filters):
    if not filters.get("has_target_type"):
        filters.has_target_type = "Item"
    if not filters.get("missing_target_type"):
        filters.missing_target_type = "Item"

    for fieldname in ("has_target_type", "missing_target_type"):
        if filters.get(fieldname) not in ("Item", "Item Group"):
            frappe.throw(_("{0} must be Item or Item Group").format(fieldname))

    required = ["company", "from_date", "to_date"]
    missing = [field for field in required if not filters.get(field)]
    if missing:
        frappe.throw(_("Missing required filters: {0}").format(", ".join(missing)))

    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date cannot be after To Date"))

    if not get_missing_target_message(filters) and get_target_identity(filters, "has") == get_target_identity(filters, "missing"):
        frappe.throw(_("Buys Target and Missing Target must be different"))


def get_columns():
    return [
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 140},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 220},
        {"label": _("Territory"), "fieldname": "territory", "fieldtype": "Link", "options": "Territory", "width": 130},
        {"label": _("City"), "fieldname": "city", "fieldtype": "Data", "width": 120},
        {"label": _("State"), "fieldname": "state", "fieldtype": "Data", "width": 130},
        {"label": _("Customer Group"), "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 150},
        {"label": _("Sales Person"), "fieldname": "sales_person", "fieldtype": "Data", "width": 180},
        {"label": _("Buys Target Qty"), "fieldname": "has_item_qty", "fieldtype": "Float", "width": 130},
        {"label": _("Buys Target Value"), "fieldname": "has_item_value", "fieldtype": "Currency", "width": 140},
        {"label": _("Missing Target Qty"), "fieldname": "missing_item_qty", "fieldtype": "Float", "width": 140},
        {"label": _("Last Bought Target"), "fieldname": "last_has_item_date", "fieldtype": "Date", "width": 150},
        {"label": _("Opportunity"), "fieldname": "opportunity", "fieldtype": "Data", "width": 120},
    ]


def get_data(filters):
    conditions, params = get_customer_conditions(filters)
    has_target_condition = get_target_condition(filters, "has")
    missing_target_condition = get_target_condition(filters, "missing")

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
                AND {has_target_condition}
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
                AND {missing_target_condition}
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
    }
    add_target_params(filters, params, "has")
    add_target_params(filters, params, "missing")
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


def get_missing_target_message(filters):
    missing = []
    for prefix, label in (("has", _("Buys Target")), ("missing", _("Missing Target"))):
        target_type = filters.get(f"{prefix}_target_type")
        if target_type == "Item" and not filters.get(f"{prefix}_item_code"):
            missing.append(_("{0} Item").format(label))
        elif target_type == "Item Group" and not filters.get(f"{prefix}_item_group"):
            missing.append(_("{0} Item Group").format(label))

    if not missing:
        return None

    return _("Please select: {0}").format(", ".join(missing))


def get_target_identity(filters, prefix):
    target_type = filters.get(f"{prefix}_target_type")
    if target_type == "Item":
        return target_type, filters.get(f"{prefix}_item_code")
    return target_type, filters.get(f"{prefix}_item_group")


def add_target_params(filters, params, prefix):
    target_type = filters.get(f"{prefix}_target_type")
    if target_type == "Item":
        params[f"{prefix}_item_code"] = filters.get(f"{prefix}_item_code")
    else:
        params[f"{prefix}_item_group"] = filters.get(f"{prefix}_item_group")


def get_target_condition(filters, prefix):
    target_type = filters.get(f"{prefix}_target_type")
    if target_type == "Item":
        return f"sii.item_code = %({prefix}_item_code)s"

    return f"""
        EXISTS (
            SELECT 1
            FROM `tabItem` target_item
            INNER JOIN `tabItem Group` item_group
                ON item_group.name = target_item.item_group
            INNER JOIN `tabItem Group` selected_group
                ON selected_group.name = %({prefix}_item_group)s
            WHERE
                target_item.name = sii.item_code
                AND item_group.lft >= selected_group.lft
                AND item_group.rgt <= selected_group.rgt
        )
    """


def get_summary(data):
    return [
        {"label": _("Opportunities"), "value": len(data), "indicator": "Orange", "datatype": "Int"},
        {"label": _("Base Target Qty"), "value": sum(row.get("has_item_qty") or 0 for row in data), "indicator": "Blue", "datatype": "Float"},
        {"label": _("Base Target Value"), "value": sum(row.get("has_item_value") or 0 for row in data), "indicator": "Green", "datatype": "Currency"},
    ]
