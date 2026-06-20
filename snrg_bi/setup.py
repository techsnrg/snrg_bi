import json

import frappe


MODULE_NAME = "SNRG BI"
APP_NAME = "snrg_bi"

REPORTS = [
    {
        "report_name": "Customer Item Gap",
        "ref_doctype": "Customer",
        "roles": ["Sales User", "Sales Manager", "System Manager"],
    },
    {
        "report_name": "Customer Basket Gap",
        "ref_doctype": "Customer",
        "roles": ["Sales User", "Sales Manager", "System Manager"],
    },
    {
        "report_name": "Dropped Item Customers",
        "ref_doctype": "Customer",
        "roles": ["Sales User", "Sales Manager", "System Manager"],
    },
    {
        "report_name": "Item Penetration by City",
        "ref_doctype": "Customer",
        "roles": ["Sales User", "Sales Manager", "System Manager"],
    },
    {
        "report_name": "Salesperson Item Opportunities",
        "ref_doctype": "Customer",
        "roles": ["Sales User", "Sales Manager", "System Manager"],
    },
]


def after_install():
    _ensure_module()
    _ensure_customer_market_fields()
    _ensure_reports()
    _ensure_workspace()
    frappe.db.commit()


def after_migrate():
    _ensure_module()
    _ensure_customer_market_fields()
    _ensure_reports()
    _ensure_workspace()
    frappe.db.commit()


def _ensure_module():
    if frappe.db.exists("Module Def", MODULE_NAME):
        frappe.db.set_value(
            "Module Def",
            MODULE_NAME,
            "app_name",
            APP_NAME,
            update_modified=False,
        )
        return

    frappe.get_doc(
        {
            "doctype": "Module Def",
            "module_name": MODULE_NAME,
            "app_name": APP_NAME,
        }
    ).insert(ignore_permissions=True)


def _ensure_reports():
    for report_def in REPORTS:
        report_name = report_def["report_name"]
        roles = report_def["roles"]

        if frappe.db.exists("Report", report_name):
            frappe.db.set_value(
                "Report",
                report_name,
                {
                    "module": MODULE_NAME,
                    "report_type": "Script Report",
                    "ref_doctype": report_def["ref_doctype"],
                    "is_standard": "Yes",
                    "disabled": 0,
                    "prepared_report": 0,
                },
                update_modified=False,
            )
            _ensure_report_roles(report_name, roles)
            continue

        frappe.get_doc(
            {
                "doctype": "Report",
                "report_name": report_name,
                "report_type": "Script Report",
                "ref_doctype": report_def["ref_doctype"],
                "module": MODULE_NAME,
                "is_standard": "Yes",
                "disabled": 0,
                "prepared_report": 0,
                "roles": [{"role": role} for role in roles],
            }
        ).insert(ignore_permissions=True)


def _ensure_customer_market_fields():
    fields = [
        {
            "fieldname": "custom_city",
            "fieldtype": "Data",
            "label": "City",
            "insert_after": "mobile_no",
            "in_standard_filter": 1,
        },
        {
            "fieldname": "custom_state",
            "fieldtype": "Data",
            "label": "State",
            "insert_after": "custom_city",
            "in_standard_filter": 1,
        },
    ]

    for field_def in fields:
        _ensure_custom_field("Customer", field_def)


def _ensure_custom_field(doctype, field_def):
    meta = frappe.get_meta(doctype)
    fieldname = field_def["fieldname"]
    custom_field_name = f"{doctype}-{fieldname}"

    if meta.has_field(fieldname) or frappe.db.exists("Custom Field", custom_field_name):
        return

    field_def = _resolve_custom_field_layout_anchor(doctype, field_def)
    doc = {"doctype": "Custom Field", "dt": doctype}
    doc.update(field_def)
    frappe.get_doc(doc).insert(ignore_permissions=True)


def _resolve_custom_field_layout_anchor(doctype, field_def):
    field_def = dict(field_def)
    anchor = field_def.get("insert_after")
    if not anchor:
        return field_def

    if frappe.get_meta(doctype).has_field(anchor):
        return field_def

    if frappe.db.exists("Custom Field", f"{doctype}-{anchor}"):
        return field_def

    field_def.pop("insert_after", None)
    return field_def


def _ensure_report_roles(report_name, roles):
    report = frappe.get_doc("Report", report_name)
    existing_roles = {row.role for row in report.roles}
    missing_roles = [role for role in roles if role not in existing_roles]
    if not missing_roles:
        return

    for role in missing_roles:
        report.append("roles", {"role": role})
    report.save(ignore_permissions=True)


def _ensure_workspace():
    workspace_name = "SNRG BI"
    shortcuts = [
        {
            "id": "customer_item_gap_shortcut",
            "shortcut_name": "Customer Item Gap",
        },
        {
            "id": "customer_basket_gap_shortcut",
            "shortcut_name": "Customer Basket Gap",
        },
        {
            "id": "dropped_item_customers_shortcut",
            "shortcut_name": "Dropped Item Customers",
        },
        {
            "id": "item_penetration_by_city_shortcut",
            "shortcut_name": "Item Penetration by City",
        },
        {
            "id": "salesperson_item_opportunities_shortcut",
            "shortcut_name": "Salesperson Item Opportunities",
        },
    ]
    content = [
        {
            "id": "snrg_bi_header",
            "type": "header",
            "data": {"text": "SNRG BI", "col": 12},
        }
    ] + [
        {
            "id": shortcut["id"],
            "type": "shortcut",
            "data": {"shortcut_name": shortcut["shortcut_name"], "col": 3},
        }
        for shortcut in shortcuts
    ]

    links = [
        {
            "label": "Sales Reports",
            "type": "Card Break",
            "hidden": 0,
            "onboard": 0,
            "link_count": 0,
            "is_query_report": 0,
        }
    ] + [
        {
            "label": report["report_name"],
            "type": "Link",
            "link_type": "Report",
            "link_to": report["report_name"],
            "hidden": 0,
            "onboard": 1,
            "link_count": 0,
            "is_query_report": 0,
        }
        for report in REPORTS
    ]

    workspace_shortcuts = [
        {
            "label": report["report_name"],
            "type": "Report",
            "link_to": report["report_name"],
            "color": "Blue",
        }
        for report in REPORTS
    ]

    doc = {
        "doctype": "Workspace",
        "name": workspace_name,
        "label": workspace_name,
        "module": MODULE_NAME,
        "category": "Modules",
        "icon": "bar-chart",
        "public": 1,
        "is_hidden": 0,
        "developer_mode_only": 0,
        "content": json.dumps(content),
        "links": links,
        "shortcuts": workspace_shortcuts,
    }

    if frappe.db.exists("Workspace", workspace_name):
        workspace = frappe.get_doc("Workspace", workspace_name)
        for key, value in doc.items():
            if key in ("doctype", "links", "shortcuts"):
                continue
            setattr(workspace, key, value)

        workspace.set("links", [])
        for link in links:
            workspace.append("links", link)

        workspace.set("shortcuts", [])
        for shortcut in workspace_shortcuts:
            workspace.append("shortcuts", shortcut)

        workspace.save(ignore_permissions=True)
        return

    frappe.get_doc(doc).insert(ignore_permissions=True)
