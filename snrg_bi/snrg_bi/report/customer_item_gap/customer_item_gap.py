import frappe
from frappe import _
from frappe.utils import add_months


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)

    columns = get_columns()
    data = get_data(filters)
    summary = get_summary(data)

    return columns, data, None, None, summary


def validate_filters(filters):
    required = ["company", "from_date", "to_date", "item_code"]
    missing = [field for field in required if not filters.get(field)]
    if missing:
        frappe.throw(_("Missing required filters: {0}").format(", ".join(missing)))

    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date cannot be after To Date"))

    selected_status_filters = [
        label
        for label, fieldname in (
            (_("Buyers Only"), "buyers_only"),
            (_("Stopped Buying Only"), "stopped_buying_only"),
            (_("Opportunities Only"), "opportunities_only"),
        )
        if filters.get(fieldname)
    ]
    if len(selected_status_filters) > 1:
        frappe.throw(_("Select only one status filter: {0}").format(", ".join(selected_status_filters)))

    if not filters.get("dropped_lookback_months"):
        filters.dropped_lookback_months = 12

    try:
        filters.dropped_lookback_months = int(filters.dropped_lookback_months)
    except (TypeError, ValueError):
        frappe.throw(_("Dropped Lookback must be a valid month count"))

    if filters.dropped_lookback_months not in (1, 2, 3, 6, 9, 12):
        frappe.throw(_("Dropped Lookback must be 1, 2, 3, 6, 9, or 12 months"))


def get_columns():
    return [
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 140},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 220},
        {"label": _("Territory"), "fieldname": "territory", "fieldtype": "Link", "options": "Territory", "width": 130},
        {"label": _("City"), "fieldname": "city", "fieldtype": "Data", "width": 120},
        {"label": _("State"), "fieldname": "state", "fieldtype": "Data", "width": 130},
        {"label": _("Customer Group"), "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 150},
        {"label": _("Sales Person"), "fieldname": "sales_person", "fieldtype": "Data", "width": 180},
        {"label": _("Bought Item"), "fieldname": "bought_item", "fieldtype": "Data", "width": 100},
        {"label": _("Qty Bought"), "fieldname": "qty_bought", "fieldtype": "Float", "width": 110},
        {"label": _("Sales Value"), "fieldname": "sales_value", "fieldtype": "Currency", "width": 130},
        {"label": _("Last Purchase Date"), "fieldname": "last_purchase_date", "fieldtype": "Date", "width": 140},
        {"label": _("Other Items Bought"), "fieldname": "other_items_bought", "fieldtype": "Data", "width": 260},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
    ]


def get_data(filters):
    conditions, params = get_customer_conditions(filters)
    params["dropped_from_date"] = add_months(filters.from_date, -filters.dropped_lookback_months)

    query = f"""
        SELECT
            c.name AS customer,
            c.customer_name,
            c.territory,
            c.custom_city AS city,
            c.custom_state AS state,
            c.customer_group,
            sales_team.sales_person,
            CASE WHEN item_sales.qty_bought > 0 THEN 'Yes' ELSE 'No' END AS bought_item,
            COALESCE(item_sales.qty_bought, 0) AS qty_bought,
            COALESCE(item_sales.sales_value, 0) AS sales_value,
            item_sales.last_purchase_date,
            other_items.other_items_bought,
            CASE
                WHEN item_sales.qty_bought > 0 THEN 'Buyer'
                WHEN prior_sales.last_purchase_date IS NOT NULL THEN 'Stopped Buying'
                ELSE 'Opportunity'
            END AS status
        FROM `tabCustomer` c
        LEFT JOIN (
            SELECT
                parent,
                GROUP_CONCAT(DISTINCT sales_person ORDER BY sales_person SEPARATOR ', ') AS sales_person
            FROM `tabSales Team`
            WHERE parenttype = 'Customer'
            GROUP BY parent
        ) sales_team ON sales_team.parent = c.name
        LEFT JOIN (
            SELECT
                si.customer,
                SUM(sii.qty) AS qty_bought,
                SUM(sii.base_net_amount) AS sales_value,
                MAX(si.posting_date) AS last_purchase_date
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
        LEFT JOIN (
            SELECT
                si.customer,
                SUBSTRING_INDEX(
                    GROUP_CONCAT(DISTINCT sii.item_code ORDER BY sii.item_code SEPARATOR ', '),
                    ', ',
                    20
                ) AS other_items_bought
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            WHERE
                si.docstatus = 1
                AND COALESCE(si.is_return, 0) = 0
                AND si.company = %(company)s
                AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND sii.item_code != %(item_code)s
            GROUP BY si.customer
        ) other_items ON other_items.customer = c.name
        LEFT JOIN (
            SELECT
                si.customer,
                MAX(si.posting_date) AS last_purchase_date
            FROM `tabSales Invoice` si
            INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
            WHERE
                si.docstatus = 1
                AND COALESCE(si.is_return, 0) = 0
                AND si.company = %(company)s
                AND si.posting_date >= %(dropped_from_date)s
                AND si.posting_date < %(from_date)s
                AND sii.item_code = %(item_code)s
            GROUP BY si.customer
        ) prior_sales ON prior_sales.customer = c.name
        WHERE {conditions}
        ORDER BY
            bought_item ASC,
            sales_value DESC,
            c.customer_name ASC
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

    if filters.get("territory"):
        conditions.append("c.territory = %(territory)s")
        params["territory"] = filters.territory

    if filters.get("city"):
        conditions.append("c.custom_city = %(city)s")
        params["city"] = filters.city

    if filters.get("state"):
        conditions.append("c.custom_state = %(state)s")
        params["state"] = filters.state

    if filters.get("customer_group"):
        conditions.append("c.customer_group = %(customer_group)s")
        params["customer_group"] = filters.customer_group

    if filters.get("sales_person"):
        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM `tabSales Team` st
                WHERE
                    st.parenttype = 'Customer'
                    AND st.parent = c.name
                    AND st.sales_person = %(sales_person)s
            )
            """
        )
        params["sales_person"] = filters.sales_person

    if filters.get("buyers_only"):
        conditions.append("COALESCE(item_sales.qty_bought, 0) > 0")

    if filters.get("stopped_buying_only"):
        conditions.append("COALESCE(item_sales.qty_bought, 0) = 0")
        conditions.append("prior_sales.last_purchase_date IS NOT NULL")

    if filters.get("opportunities_only"):
        conditions.append("COALESCE(item_sales.qty_bought, 0) = 0")
        conditions.append("prior_sales.last_purchase_date IS NULL")

    return " AND ".join(conditions), params


def get_summary(data):
    buyers = len([row for row in data if row.get("bought_item") == "Yes"])
    opportunities = len([row for row in data if row.get("status") == "Opportunity"])
    stopped_buying = len([row for row in data if row.get("status") == "Stopped Buying"])
    total_qty = sum(row.get("qty_bought") or 0 for row in data)
    total_value = sum(row.get("sales_value") or 0 for row in data)

    return [
        {"label": _("Customers"), "value": len(data), "indicator": "Blue", "datatype": "Int"},
        {"label": _("Buyers"), "value": buyers, "indicator": "Green", "datatype": "Int"},
        {"label": _("Opportunities"), "value": opportunities, "indicator": "Orange", "datatype": "Int"},
        {"label": _("Stopped Buying"), "value": stopped_buying, "indicator": "Red", "datatype": "Int"},
        {"label": _("Qty Bought"), "value": total_qty, "indicator": "Blue", "datatype": "Float"},
        {"label": _("Sales Value"), "value": total_value, "indicator": "Green", "datatype": "Currency"},
    ]
