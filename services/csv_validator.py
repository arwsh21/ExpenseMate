import csv
import io

from exceptions import ValidationError
from services import money
from services import validators


REQUIRED_HEADER = ["date", "category", "amount", "type"]


def validate_csv_file(file_bytes, category_lookup):
    errors = []
    rows = []


    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        errors.append({"row": 0, "problem": "The file is not valid UTF-8 text. Please save it as a UTF-8 CSV file."})
        return {"valid": False, "errors": errors, "rows": []}

    if text.strip() == "":
        errors.append({"row": 0, "problem": "The file is empty."})
        return {"valid": False, "errors": errors, "rows": []}


    reader = csv.reader(io.StringIO(text))


    try:
        header = next(reader)
    except (StopIteration, csv.Error):
        errors.append({"row": 0, "problem": "The file could not be read as a CSV file."})
        return {"valid": False, "errors": errors, "rows": []}

    header_errors = check_header(header)
    if len(header_errors) > 0:
        return {"valid": False, "errors": header_errors, "rows": []}


    data_row_count = 0

    try:
        for values in reader:


            row_number = reader.line_num


            if len(values) == 0:
                continue

            data_row_count = data_row_count + 1

            row_errors, cleaned_row = check_row(values, row_number, category_lookup)
            if len(row_errors) > 0:
                errors.extend(row_errors)
            else:
                rows.append(cleaned_row)
    except csv.Error:
        errors.append({"row": 0, "problem": "The file could not be read as a CSV file. Please check its format."})
        return {"valid": False, "errors": errors, "rows": []}


    if data_row_count == 0:
        errors.append({"row": 0, "problem": "The file has a header but no transactions."})

    if len(errors) > 0:
        return {"valid": False, "errors": errors, "rows": []}

    return {"valid": True, "errors": [], "rows": rows}


def check_header(header):
    problems = []


    missing = []
    for column in REQUIRED_HEADER:
        if column not in header:
            missing.append(column)


    extra = []
    for column in header:
        if column not in REQUIRED_HEADER:
            extra.append(column)

    if len(missing) > 0:
        problems.append({
            "row": 0,
            "problem": "Missing required column(s): " + ", ".join(missing) + ".",
        })

    if len(extra) > 0:
        problems.append({
            "row": 0,
            "problem": "Unexpected extra column(s): " + ", ".join(extra) + ".",
        })


    if len(problems) == 0 and header != REQUIRED_HEADER:
        problems.append({
            "row": 0,
            "problem": "The columns must be in this exact order: " + ",".join(REQUIRED_HEADER) + ".",
        })

    return problems


def check_row(values, row_number, category_lookup):
    problems = []

    if len(values) != len(REQUIRED_HEADER):
        problems.append({
            "row": row_number,
            "problem": "Expected " + str(len(REQUIRED_HEADER)) + " values but found "
                       + str(len(values)) + ".",
        })
        return problems, None

    date_text = values[0]
    category_text = values[1]
    amount_text = values[2]
    type_text = values[3]

    cleaned = {}


    try:
        cleaned["date"] = validators.parse_date(date_text)
    except ValidationError as error:
        for message in error.messages:
            problems.append({"row": row_number, "problem": message})


    category_key = category_text.strip().lower()
    if category_key in category_lookup:
        cleaned["category_id"] = category_lookup[category_key]
    else:
        problems.append({
            "row": row_number,
            "problem": "Category '" + category_text.strip() + "' does not exist. "
                       "Create it on the Categories page first.",
        })


    try:
        cleaned["amount_minor"] = money.parse_amount(amount_text, "Amount")
    except ValidationError as error:
        for message in error.messages:
            problems.append({"row": row_number, "problem": message})


    try:
        cleaned["type"] = validators.parse_type(type_text)
    except ValidationError:
        problems.append({
            "row": row_number,
            "problem": "Type must be 'income' or 'expense' in lowercase (found '" + type_text + "').",
        })

    if len(problems) > 0:
        return problems, None

    return problems, cleaned
