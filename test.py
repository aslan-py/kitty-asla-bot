import sqlite3
from config import DATABASE_NAME
import requests
import pprint

def other_category_values():
    """Выгружает все названия из категории other."""

    con = sqlite3.connect(DATABASE_NAME)
    cur = con.cursor()

    categories = cur.execute(
            'SELECT title FROM products WHERE category_id = 10')
    title_other = categories.fetchall()
    for title in title_other:
        print(title[0])

# other_category_values()
