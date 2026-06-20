import frappe

from snrg_bi.snrg_bi.report.customer_basket_gap.customer_basket_gap import execute as customer_basket_gap
from snrg_bi.snrg_bi.report.customer_item_gap.customer_item_gap import execute as customer_item_gap
from snrg_bi.snrg_bi.report.dropped_item_customers.dropped_item_customers import execute as dropped_item_customers
from snrg_bi.snrg_bi.report.item_penetration_by_city.item_penetration_by_city import execute as item_penetration_by_city
from snrg_bi.snrg_bi.report.salesperson_item_opportunities.salesperson_item_opportunities import (
    execute as salesperson_item_opportunities,
)


REPORT_TOOLS = {
    "customer_item_gap": customer_item_gap,
    "customer_basket_gap": customer_basket_gap,
    "dropped_item_customers": dropped_item_customers,
    "item_penetration_by_city": item_penetration_by_city,
    "salesperson_item_opportunities": salesperson_item_opportunities,
}


@frappe.whitelist()
def run_report_tool(tool_name, filters=None):
    """Approved report execution surface for future AI/chat integrations."""
    if tool_name not in REPORT_TOOLS:
        frappe.throw(f"Unsupported report tool: {tool_name}")

    parsed_filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
    columns, data, message, chart, summary = REPORT_TOOLS[tool_name](parsed_filters)

    return {
        "columns": columns,
        "data": data,
        "message": message,
        "chart": chart,
        "summary": summary,
    }


@frappe.whitelist()
def get_available_report_tools():
    return [
        {
            "name": "customer_item_gap",
            "description": "Customers buying or not buying a selected item in a selected market.",
            "required_filters": ["company", "from_date", "to_date", "item_code"],
        },
        {
            "name": "customer_basket_gap",
            "description": "Customers buying one item but not another item.",
            "required_filters": ["company", "from_date", "to_date", "has_item_code", "missing_item_code"],
        },
        {
            "name": "dropped_item_customers",
            "description": "Customers who bought an item earlier but stopped in the selected period.",
            "required_filters": ["company", "from_date", "to_date", "item_code"],
        },
        {
            "name": "item_penetration_by_city",
            "description": "City-wise item penetration and opportunity counts.",
            "required_filters": ["company", "from_date", "to_date", "item_code"],
        },
        {
            "name": "salesperson_item_opportunities",
            "description": "Salesperson-wise buying and non-buying customers for a selected item.",
            "required_filters": ["company", "from_date", "to_date", "item_code"],
        },
    ]

