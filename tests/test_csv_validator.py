from services import csv_validator


CATEGORIES = {"food": 1, "rent": 2, "other": 3, "food, drinks": 4}

HEADER = "date,category,amount,type\n"


def validate(csv_text):
    return csv_validator.validate_csv_file(csv_text.encode("utf-8"), CATEGORIES)


def all_problems(result):
    texts = []
    for error in result["errors"]:
        texts.append(error["problem"])
    return " | ".join(texts)


def test_valid_file_gives_clean_rows():
    result = validate(HEADER + "2026-09-01,Food,450,expense\n2026-09-02,Other,50000.50,income\n")

    assert result["valid"] is True
    assert result["errors"] == []
    assert result["rows"] == [
        {"date": "2026-09-01", "category_id": 1, "amount_minor": 45000, "type": "expense"},
        {"date": "2026-09-02", "category_id": 3, "amount_minor": 5000050, "type": "income"},
    ]


def test_category_is_matched_after_trimming_and_ignoring_case():
    result = validate(HEADER + "2026-09-01,  fOOd  ,10,expense\n")

    assert result["valid"] is True
    assert result["rows"][0]["category_id"] == 1


def test_quoted_category_containing_a_comma_is_read_correctly():
    result = validate(HEADER + '2026-09-01,"Food, Drinks",10,expense\n')

    assert result["valid"] is True
    assert result["rows"][0]["category_id"] == 4


def test_future_dates_are_allowed():
    result = validate(HEADER + "2030-01-15,Food,10,expense\n")

    assert result["valid"] is True


def test_file_with_an_excel_utf8_marker_is_accepted():

    csv_bytes = b"\xef\xbb\xbf" + (HEADER + "2026-09-01,Food,10,expense\n").encode("utf-8")

    result = csv_validator.validate_csv_file(csv_bytes, CATEGORIES)

    assert result["valid"] is True


def test_blank_lines_are_skipped_but_row_numbers_stay_correct():

    result = validate(HEADER + "\n2026-09-01,Food,-5,expense\n")

    assert result["valid"] is False
    assert result["errors"][0]["row"] == 3


def test_missing_required_column_is_rejected_with_a_clear_message():
    result = validate("date,category,amount\n2026-09-01,Food,10\n")

    assert result["valid"] is False
    assert result["rows"] == []
    assert "Missing required column(s): type" in all_problems(result)


def test_extra_column_is_rejected():
    result = validate("date,category,amount,type,note\n2026-09-01,Food,10,expense,hi\n")

    assert result["valid"] is False
    assert "Unexpected extra column(s): note" in all_problems(result)


def test_columns_in_the_wrong_order_are_rejected():
    result = validate("category,date,amount,type\nFood,2026-09-01,10,expense\n")

    assert result["valid"] is False
    assert "exact order" in all_problems(result)


def test_header_names_must_match_exactly_including_case():
    result = validate("Date,category,amount,type\n2026-09-01,Food,10,expense\n")

    assert result["valid"] is False


def test_empty_file_is_rejected():
    assert validate("")["valid"] is False
    assert validate("   \n\n")["valid"] is False


def test_header_only_file_is_rejected():
    result = validate(HEADER)

    assert result["valid"] is False
    assert "no transactions" in all_problems(result)


def test_file_that_is_not_utf8_is_rejected():

    result = csv_validator.validate_csv_file(b"\xff\xfe\x00bad", CATEGORIES)

    assert result["valid"] is False
    assert "UTF-8" in all_problems(result)


def test_invalid_date_is_rejected():
    result = validate(HEADER + "2026-02-30,Food,10,expense\n")

    assert result["valid"] is False
    assert result["errors"][0]["row"] == 2
    assert "calendar date" in all_problems(result)


def test_wrongly_formatted_date_is_rejected():
    result = validate(HEADER + "01/09/2026,Food,10,expense\n")

    assert result["valid"] is False
    assert "YYYY-MM-DD" in all_problems(result)


def test_unknown_category_is_rejected():
    result = validate(HEADER + "2026-09-01,Groceries,10,expense\n")

    assert result["valid"] is False
    assert "Category 'Groceries' does not exist" in all_problems(result)


def test_negative_zero_and_non_numeric_amounts_are_rejected():
    assert "negative" in all_problems(validate(HEADER + "2026-09-01,Food,-5,expense\n"))
    assert "greater than zero" in all_problems(validate(HEADER + "2026-09-01,Food,0,expense\n"))
    assert "must be a number" in all_problems(validate(HEADER + "2026-09-01,Food,abc,expense\n"))


def test_more_than_two_decimal_places_is_rejected():
    result = validate(HEADER + "2026-09-01,Food,10.999,expense\n")

    assert result["valid"] is False
    assert "2 decimal places" in all_problems(result)


def test_type_must_be_lowercase_income_or_expense():
    assert validate(HEADER + "2026-09-01,Food,10,Expense\n")["valid"] is False
    assert validate(HEADER + "2026-09-01,Food,10,spending\n")["valid"] is False


def test_row_with_the_wrong_number_of_values_is_rejected():
    result = validate(HEADER + "2026-09-01,Food,10\n")

    assert result["valid"] is False
    assert "Expected 4 values but found 3" in all_problems(result)


def test_one_bad_row_makes_the_whole_file_invalid_and_returns_no_rows():


    result = validate(
        HEADER
        + "2026-09-01,Food,10,expense\n"
        + "2026-09-02,Food,oops,expense\n"
        + "2026-09-03,Rent,20,expense\n"
    )

    assert result["valid"] is False
    assert result["rows"] == []
    assert len(result["errors"]) == 1
    assert result["errors"][0]["row"] == 3


def test_every_bad_row_is_reported_with_its_row_number():
    result = validate(
        HEADER
        + "2026-13-01,Food,10,expense\n"
        + "2026-09-02,Food,10,expense\n"
        + "2026-09-03,Nowhere,10,expense\n"
    )

    rows_with_problems = []
    for error in result["errors"]:
        rows_with_problems.append(error["row"])

    assert rows_with_problems == [2, 4]
