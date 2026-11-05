from data import database


def get_all_categories():
    sql = "SELECT id, name FROM categories ORDER BY name COLLATE NOCASE"
    return database.fetch_all(
        sql,
        (),
        "Unable to load the categories. Please try again.",
    )


def add_category(name):


    sql = "INSERT INTO categories (name) VALUES (?)"
    result = database.execute(
        sql,
        (name,),
        "Unable to save the category. Please check the name and try again.",
    )
    return result["last_id"]
