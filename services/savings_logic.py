def calculate_totals(transactions):
    total_income = 0
    total_expenses = 0

    for transaction in transactions:
        if transaction["type"] == "income":
            total_income = total_income + transaction["amount_minor"]
        else:
            total_expenses = total_expenses + transaction["amount_minor"]

    return {
        "income_minor": total_income,
        "expense_minor": total_expenses,
        "net_minor": total_income - total_expenses,
    }


def calculate_savings(income, expenses):
    savings = income - expenses
    return savings


def calculate_monthly_summary(transactions):
    if len(transactions) == 0:
        return []


    totals_by_month = {}
    first_month = None
    last_month = None

    for transaction in transactions:
        month = transaction["date"][0:7]

        if month not in totals_by_month:
            totals_by_month[month] = {"income_minor": 0, "expense_minor": 0}

        if transaction["type"] == "income":
            totals_by_month[month]["income_minor"] += transaction["amount_minor"]
        else:
            totals_by_month[month]["expense_minor"] += transaction["amount_minor"]


        if first_month is None or month < first_month:
            first_month = month
        if last_month is None or month > last_month:
            last_month = month


    year = int(first_month[0:4])
    month_number = int(first_month[5:7])

    summary = []
    while True:
        month_text = f"{year:04d}-{month_number:02d}"

        income = 0
        expenses = 0
        if month_text in totals_by_month:
            income = totals_by_month[month_text]["income_minor"]
            expenses = totals_by_month[month_text]["expense_minor"]

        summary.append({
            "month": month_text,
            "income_minor": income,
            "expense_minor": expenses,
            "savings_minor": calculate_savings(income, expenses),
        })

        if month_text == last_month:
            break


        month_number = month_number + 1
        if month_number > 12:
            month_number = 1
            year = year + 1

    return summary
