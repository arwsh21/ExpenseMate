from exceptions import ValidationError


MAX_WHOLE_DIGITS = 12


def parse_amount(text, field_name="Amount"):
    if text is None:
        text = ""
    text = str(text).strip()

    if text == "":
        raise ValidationError(field_name + " is required.")


    if text.startswith("-"):
        raise ValidationError(field_name + " cannot be negative.")


    allowed_characters = "0123456789."
    for character in text:
        if character not in allowed_characters:
            raise ValidationError(
                field_name + " must be a number such as 450 or 450.50 "
                "(digits and one decimal point only)."
            )

    if text.count(".") > 1:
        raise ValidationError(
            field_name + " must be a number such as 450 or 450.50 "
            "(digits and one decimal point only)."
        )


    parts = text.split(".")
    whole_part = parts[0]
    fraction_part = ""
    if len(parts) == 2:
        fraction_part = parts[1]

    if whole_part == "" and fraction_part == "":
        raise ValidationError(
            field_name + " must be a number such as 450 or 450.50."
        )

    if len(fraction_part) > 2:
        raise ValidationError(field_name + " can have at most 2 decimal places.")

    if len(whole_part) > MAX_WHOLE_DIGITS:
        raise ValidationError(field_name + " is too large.")


    if whole_part == "":
        whole_part = "0"
    while len(fraction_part) < 2:
        fraction_part = fraction_part + "0"

    minor_units = int(whole_part) * 100 + int(fraction_part)

    if minor_units <= 0:
        raise ValidationError(field_name + " must be greater than zero.")

    return minor_units


def minor_to_text(minor_units):
    sign = ""
    if minor_units < 0:
        sign = "-"
        minor_units = -minor_units

    whole_part = minor_units // 100
    fraction_part = minor_units % 100


    return f"{sign}{whole_part}.{fraction_part:02d}"


def format_amount(minor_units):
    sign = ""
    if minor_units < 0:
        sign = "-"
        minor_units = -minor_units

    whole_part = minor_units // 100
    fraction_part = minor_units % 100


    return f"{sign}{whole_part:,}.{fraction_part:02d}"
