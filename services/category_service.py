from data import category_repo
from exceptions import ValidationError
from services import validators


def get_categories():
    return category_repo.get_all_categories()


def add_category(name):
    clean_name = validators.parse_category_name(name)


    existing_categories = category_repo.get_all_categories()
    for category in existing_categories:
        if category["name"].lower() == clean_name.lower():
            raise ValidationError(
                "A category named '" + category["name"] + "' already exists."
            )

    new_id = category_repo.add_category(clean_name)
    return new_id
