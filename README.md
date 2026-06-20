# SNRG BI

Custom ERPNext/Frappe master app for business intelligence reports and AI-ready reporting APIs.

## First Report

### Customer Item Gap

Answers:

> For a selected item and selected market, which customers are buying it and which customers are not?

Primary data source:

- `Customer`
- `Sales Invoice`
- `Sales Invoice Item`
- `Sales Team`

Market fields:

- `Customer.territory`
- `Customer.custom_city`
- `Customer.custom_state`

Sales source:

- Submitted `Sales Invoice` records (`docstatus = 1`)
- Excludes return invoices by default (`is_return = 0`)

## Initial Report Family

- `Customer Item Gap`: who buys / does not buy a selected item.
- `Customer Basket Gap`: customers buying one item but not another.
- `Dropped Item Customers`: customers who bought an item earlier but stopped.
- `Item Penetration by City`: city-wise penetration and opportunity count.
- `Salesperson Item Opportunities`: salesperson-wise opportunity list.

## AI Base

The app includes an approved AI-facing tool layer at `snrg_bi.ai.report_tools`.

This lets a future chat/AI interface call trusted report tools such as:

- `customer_item_gap`
- `customer_basket_gap`
- `dropped_item_customers`
- `item_penetration_by_city`
- `salesperson_item_opportunities`

The AI layer should call these approved tools rather than querying raw ERPNext tables directly.

## Customer Item Gap Status Logic

- `Buyer`: bought the selected item during the selected report period.
- `Stopped Buying`: did not buy the selected item during the report period, but bought it within the selected dropped lookback window before the report period.
- `Opportunity`: did not buy the selected item during the report period and did not buy it within the selected dropped lookback window.

The dropped lookback window supports 1, 2, 3, 6, 9, or 12 months. This prevents very old purchases from years ago being treated as current dropped customers.

## Frappe Cloud Deployment

This app is scaffolded as a standard Frappe Cloud-friendly app:

- root `pyproject.toml` and `setup.py` for Python package installation
- `snrg_bi/hooks.py` for Frappe app metadata
- `snrg_bi/setup.py` for idempotent install/migrate setup
- standard report files under `snrg_bi/snrg_bi/report`
- workspace files under `snrg_bi/snrg_bi/workspace`

Install flow:

1. Push this repository to GitHub.
2. Add the GitHub app repository to the Frappe Cloud bench.
3. Install the app on the target site.
4. Run migrate if Frappe Cloud does not do it automatically.
5. Open Desk and search for `Customer Item Gap`.

The install/migrate hook ensures:

- `Module Def`: SNRG BI
- `Customer` custom fields if missing: `custom_city`, `custom_state`
- reports listed in `snrg_bi/setup.py`
- `Workspace`: SNRG BI

## Local Bench Commands

If testing on a local bench:

```bash
bench get-app snrg_bi <github-url>
bench --site <site-name> install-app snrg_bi
bench --site <site-name> migrate
```
