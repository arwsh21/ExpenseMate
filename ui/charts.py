from matplotlib.figure import Figure


COLOR_BUDGET = "#4338CA"
COLOR_SPENT = "#F59E0B"
COLOR_REMAINING = "#0F766E"
COLOR_INCOME = "#16A34A"
COLOR_EXPENSE = "#DC2626"
COLOR_SAVINGS = "#4338CA"


def create_budget_chart(status_list):
    figure = Figure(figsize=(9, 4.6))
    axes = figure.subplots()

    names = []
    budget_values = []
    spent_values = []
    remaining_values = []
    positions = []


    for index in range(len(status_list)):
        status = status_list[index]
        names.append(status["category_name"])
        budget_values.append(status["limit_minor"] / 100)
        spent_values.append(status["spent_minor"] / 100)
        remaining_values.append(status["remaining_minor"] / 100)
        positions.append(index)

    bar_width = 0.26


    budget_positions = []
    spent_positions = []
    remaining_positions = []
    for position in positions:
        budget_positions.append(position - bar_width)
        spent_positions.append(position)
        remaining_positions.append(position + bar_width)

    axes.bar(budget_positions, budget_values, bar_width, label="Budget", color=COLOR_BUDGET)
    axes.bar(spent_positions, spent_values, bar_width, label="Spent", color=COLOR_SPENT)
    axes.bar(remaining_positions, remaining_values, bar_width, label="Remaining", color=COLOR_REMAINING)

    axes.set_xticks(positions)
    axes.set_xticklabels(names)
    axes.set_ylabel("Amount")
    axes.set_title("Budget, spent and remaining by category (this month)")
    axes.axhline(0, color="#94A3B8", linewidth=0.8)
    axes.legend()
    style_axes(axes)
    figure.tight_layout()
    return figure


def create_trend_chart(monthly_summary):
    figure = Figure(figsize=(10, 4.8))
    axes = figure.subplots()

    months = []
    income_values = []
    expense_values = []
    savings_values = []
    positions = []

    for index in range(len(monthly_summary)):
        row = monthly_summary[index]
        months.append(row["month"])
        income_values.append(row["income_minor"] / 100)
        expense_values.append(row["expense_minor"] / 100)
        savings_values.append(row["savings_minor"] / 100)
        positions.append(index)

    bar_width = 0.26

    income_positions = []
    expense_positions = []
    savings_positions = []
    for position in positions:
        income_positions.append(position - bar_width)
        expense_positions.append(position)
        savings_positions.append(position + bar_width)

    axes.bar(income_positions, income_values, bar_width, label="Income", color=COLOR_INCOME)
    axes.bar(expense_positions, expense_values, bar_width, label="Expenses", color=COLOR_EXPENSE)
    axes.bar(savings_positions, savings_values, bar_width, label="Savings", color=COLOR_SAVINGS)


    step = 1
    if len(months) > 12:
        step = len(months) // 12 + 1

    tick_positions = []
    tick_labels = []
    for index in range(0, len(months), step):
        tick_positions.append(index)
        tick_labels.append(months[index])

    axes.set_xticks(tick_positions)
    axes.set_xticklabels(tick_labels, rotation=45, ha="right")
    axes.set_ylabel("Amount")
    axes.set_title("Income, expenses and savings by month")
    axes.axhline(0, color="#94A3B8", linewidth=0.8)
    axes.legend()
    style_axes(axes)
    figure.tight_layout()
    return figure


def style_axes(axes):
    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)
    axes.yaxis.grid(True, color="#E2E8F0")
    axes.set_axisbelow(True)
