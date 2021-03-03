from cs50 import SQL

"""
quick script to add list of categories
to database
note: to be executed once!
"""
db = SQL("sqlite:///project.db")

categories = [
    "Vehicles",
    "Properties",
    "Mobile Phones, Tablets, Accessories",
    "Electronics & Home Appliances",
    "Home Furniture - Decor",
    "Fashion & Beauty",
    "Pets - Accessories",
    "Kids & Babies",
    "Books, Sports & Hobbies",
    "Business - Industrial - Agriculture",
    "Food & Nutrition"
    ]

# add categoriees to db
for cat in categories:
    db.execute("INSERT INTO categories(name) VALUES(?)", cat)

rows = db.execute("SELECT * FROM categories")
print(rows)