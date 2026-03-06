"""
Balance Sheet / Fund Dashboard metrics.

Calculates key financial metrics for a given fund by aggregating
the totals collection across all properties linked to that fund.

Account mappings (ROW_*) reference the chart-of-accounts IDs used in
the legacy system. Adjust these lists as needed to match your GL setup.
"""

from app.database import totals_col, funds_col, fund_properties_col, properties_col
from app.logger import get_logger
from app.database import balance_sheet_col
logger = get_logger("models.balancesheet")

# ---------------------------------------------------------------------------
# Account ID mappings – each row references one or more GL account IDs.
# These correspond to the balance-sheet / income-statement row numbers
# used in the legacy reporting system.
# ---------------------------------------------------------------------------

# Balance Sheet – Assets
ROW_27_INVESTMENTS_LP = [3511, 3660, 3715, 3719, 3723, 3741, 3742]
ROW_30_INVESTMENTS_CORP = [3541, 3543]

# Balance Sheet – Liabilities
ROW_58_MORTGAGE_DEBT = [3576, 3588, 3600]

# Balance Sheet – Equity
ROW_69_TOTAL_EQUITY = [3744, 3819, 3833]

# Income Statement – Revenue
REVENUE_ACCOUNTS = [2961, 2963, 2975, 2982, 2990]

# Income Statement – Operating Expenses (excl. debt service & depreciation)
OPERATING_EXPENSE_ACCOUNTS = [3173, 3440, 3455, 3462, 3463]

# Income Statement – Debt Service Expenses
ROW_105_DEBT_EXPENSES = [3565, 3567]

# Income Statement – Total Fund Expenses before Depreciation and Tax
FUND_EXPENSES_BEFORE_DEPR = [3173, 3440, 3455, 3462, 3463, 3565, 3567, 3597]

# Income Statement – Net Income After Tax (Row 129)
ROW_129_NET_INCOME = [3753, 3754, 3757, 3768, 3769, 3789, 3790]

# Cash accounts
CASH_ACCOUNTS = [2928, 2930, 2943, 2954, 2960]


def _get_fund(fund_id):
    """Get all propertyLegacyIds linked to this fund."""
    fund = funds_col.find_one({"_id": __import__("bson").ObjectId(fund_id)})
    #fund = funds_col.find_one({"fundId": fund_id})
    return fund

def _get_balance_sheet(fund_id):
    """Get all balance_sheet linked to this fund."""
    balance_sheet = balance_sheet_col.find_one({"fundId": fund_id})
    print("balance_sheet ", balance_sheet)
    #fund = funds_col.find_one({"fundId": fund_id})
    return balance_sheet

def _aggregate_accounts(property_legacy_ids, account_ids, book=0):
    """Sum begin+mtd for given accounts across properties."""
    if not property_legacy_ids or not account_ids:
        return 0.0

    pipeline = [
        {
            "$match": {
                "propertyLegacyId": {"$in": property_legacy_ids},
                "accountId": {"$in": account_ids},
                "book": book,
            }
        },
        {
            "$group": {
                "_id": None,
                "totalBegin": {"$sum": "$begin"},
                "totalMtd": {"$sum": "$mtd"},
                "totalBudget": {"$sum": "$budget"},
                "totalBeginBudget": {"$sum": "$beginBudget"},
            }
        },
    ]
    result = list(totals_col.aggregate(pipeline))
    if result:
        return result[0]
    return {"totalBegin": 0.0, "totalMtd": 0.0, "totalBudget": 0.0, "totalBeginBudget": 0.0}

def get_value(_data, _id):
    result = next((item for item in _data if item["sAccountCode"] == _id), "")
    output =""
    if "newTotal" in result:
        output = result["newTotal"]
    return output

def get_balance_sheet(fund_id):
    """Calculate all balance sheet / dashboard metrics for a fund."""
    logger.info("Calculating balance sheet for fund %s", fund_id)

    fund = _get_fund(fund_id)
    if not fund:
        logger.error("Fund not found: %s", fund_id)
        return None

    logger.info("Fund %s found ", fund_id)
    logger.info("Getting balance sheet for fund %s", fund_id)
    _balance_sheet = _get_balance_sheet(fund_id)
    _data = []
    if "data" in _balance_sheet:
        _data = _balance_sheet["data"]

    # --- Calculations ---
    noi, expense_ratio, total_cash, dscr, revenue = 0, 0, 0, 0, 0
    fund_exp_actual, fund_exp_budget, budget_vs_actual= 0, 0, 0

    aum = get_value(_data, "19999999")
    total_investment_lp = get_value(_data, "15109999")
    total_investment_corp = get_value(_data, "15309999")
    eum = total_investment_lp - total_investment_corp
  
    noi = get_value(_data, "79999999")
    revenue = get_value(_data, "49999999")
    
    total_exprense = get_value(_data, "83009999") 
    expense_ratio = get_value(_data, "79999999") # Expense Ratio = Total Expenses ÷ Total Revenue 
    expense_ratio = total_exprense/ revenue

    total_cash= get_value(_data, "10009999") 

    total_debt_service =  get_value(_data, "80004999") 
    dscr = noi /total_debt_service # DSCR = NOI ÷ Total Debt Service 
    fund_exp_actual = 0  

    ytd_return = 0 #YTD Return = Net Income (YTD) ÷ Total Equity 
    net_income_after_tax =  get_value(_data, "86109999") 
    total_equity = get_value(_data, "35009999") 
    ytd_return = net_income_after_tax / total_equity
    result = {
        "fundId": fund_id,
        "fundCode": fund.get("fundCode", ""),
        "fundName": fund.get("fundName", ""),

        "aum":  round(aum, 2),

        "eum": round(eum, 2),

        "noi": round(noi, 2),
        "revenue": round(revenue, 2),
        "expenseRatio": round(expense_ratio, 4),

        "cash": round(total_cash, 2),

        "dscr":  round(dscr, 2),
        "budget_vs_actual": round(budget_vs_actual, 2),
        "budgetVsActual_details": {
            "actual": round(fund_exp_actual, 2),
            "budget": round(fund_exp_budget, 2),
            "variance": round(fund_exp_budget - fund_exp_actual, 2),
        },

        "ytdReturn": round(ytd_return, 2)

    }

    logger.info("Balance sheet calculated for fund %s: AUM=%.2f, EUM=%.2f, NOI=%.2f",
                fund_id, aum, eum, noi)
    return result
