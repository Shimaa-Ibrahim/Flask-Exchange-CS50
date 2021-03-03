import os
import json

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from helpers import login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure image uploads
UPLOAD_FOLDER = './static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

@app.route("/")
def index():
     return render_template("index.html", home_link = "active")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        messages = []
        username = request.form.get("username").strip()
        fname = request.form.get("fname").strip()
        lname = request.form.get("lname").strip()
        image = request.files['file']
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        user_exist = False
        if not username:
            messages.append("username required!")

        # check if user already exists
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) != 0:
            messages.append("username is already exists!")
            user_exist = True

        if user_exist == False:
            # if blank password or confirmation
            if not password:
                messages.append("must provide password!")

            if len(password) < 6:
                messages.append("password cannot be less than 6 characters!")

            # passwords match
            elif password != confirmation:
                messages.append("passwords do not match!")

            # user name
            if not fname:
                messages.append("first name required!")

            if not lname:
                messages.append("last name required!")

            if image and not allowed_file(image.filename):
                messages.append("allowed image extentions: png, jpeg, jpg!")

            imagename = None
            # save image
            if image and allowed_file(image.filename):
                timestamp = datetime.now().strftime("%m-%d-%Y-%H:%M:%S")
                imagename = timestamp+secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], imagename))

        # no errors
        if messages == []:
            password_hash = generate_password_hash(password)
            rows = db.execute("INSERT INTO users (username, password, fname, lname, imgURL) VALUES (?, ?, ?, ?, ?)", username, password_hash, fname, lname, imagename)
            return redirect("/login")
        else:
            flash("danger")
            flash(messages)
            return render_template("signup.html", signup_link = "active")

    else:
        return render_template("signup.html", signup_link = "active")



@app.route("/login", methods=["GET", "POST"])
def login():
    # forget user id
    session.clear()

    if request.method == "POST":
        messages = []
        # Ensure username was submitted
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        if not username :
            messages.append("Username required!")

        # Ensure password was submitted
        if not password:
            messages.append("password required!")

        # Query database for username
        if username and password:
            rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

            # Ensure username exists and password is correct
            if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
                messages = ["invalid username and/or password"]

            else:
                # Remember which user has logged in
                session["user_id"] = rows[0]["id"]
                new_row = rows[0]
                new_row.pop('password')
                session["user"] = new_row
                print(session["user"])
                # Redirect user to home page
                return redirect("/")
        # flash error messages
        flash("danger")
        flash(messages)
        return render_template("login.html", login_link = "active"), 403

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html" ,login_link ="active")


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# custom 404 error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# to add commodity
@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    """
    All categories from db
    """
    categories = db.execute("SELECT * FROM categories")

    if request.method == "POST":
        messages = []
        name = request.form.get("name").strip()
        image = request.files['file']
        seller_id = session["user_id"]
        min_price = request.form.get("minprice").strip()
        desc = request.form.get("desc")
        category = request.form.get("category")
        try:
            category = json.loads(category.replace("\'", "\""))
        except:
            messages.append("Category required!")

        # name do not exist
        if not name or len(name) < 2:
            messages.append("commodity name required!")

        # categories
        if category and category not in categories:
             messages.append("invalid category!")

        if not desc:
            messages.append("description required!")

        # minimam price do not exist
        if not min_price:
            messages.append("must provide min price!")
        try:
            min_price = float(min_price)
            if min_price < 0:
                messages.append("invalid  Price!")
        except ValueError:
             messages.append("invalid  Price!")

        if image and not allowed_file(image.filename):
            messages.append("allowed image extentions: png, jpeg, jpg!")

        imagename = None
        # save image
        if image and allowed_file(image.filename):
            timestamp = datetime.now().strftime("%m-%d-%Y-%H:%M:%S")
            imagename = timestamp + secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], imagename))

        # no errors
        if messages == []:
            rows = db.execute("INSERT INTO commodities(name, seller_id, min_price, description, img, category_id) VALUES (?, ?, ?, ?, ?, ?)", name, seller_id, min_price, desc, imagename, category['id'])
            return redirect("/myCommodities")
        else:
            flash("danger")
            flash(messages)
            return render_template("sell.html", categories= categories, sell_link = "active")
    else:
        return render_template("sell.html", categories= categories, sell_link ="active")


# my commodities
@app.route('/myCommodities')
@login_required
def myCommodities():
    # retrieve user commodities from db
    myCommodities = db.execute("SELECT commodities.*, categories.name as category FROM commodities INNER JOIN categories on commodities.category_id = categories.id  where commodities.seller_id = ?", session['user_id'])
    return render_template("myCommodities.html", commodities= myCommodities, myCommodities_link ="active")

# allow user to delete unsold commodities
@app.route('/delete/<id>/<user_id>')
@login_required
def deleteCommodity(id, user_id):
    # delete user commodity if user is the owner
    if session["user_id"] == int(user_id):
        db.execute("DELETE FROM commodities WHERE id = ?", id)
        # delete all bids for certain commoditiy
        db.execute("DELETE FROM Auctions WHERE commodity_id = ?", id)
        flash("success")
        flash(["Deleted successfully!"])
    else:
        # error
        flash('danger')
        flash(['something wrong happened! try again..'])
    return redirect("/myCommodities")


#show commodities to buy
@app.route('/<category_id>', defaults={'category_id': None})
@app.route('/buy/<category_id>')
@login_required
def buy(category_id = None):
    categories = db.execute("SELECT * FROM categories")
    # if no specific category retrieve all allowed commodities from db
    if not category_id:
        Commodities = db.execute("SELECT commodities.*, categories.name as category FROM commodities INNER JOIN categories on commodities.category_id = categories.id  WHERE commodities.seller_id != ? AND commodities.buyer_id IS NULL", session['user_id'])
    else:
        try:
            category_id = int(category_id)
            # retrieve specific category
            Commodities = db.execute("SELECT commodities.*, categories.name as category FROM commodities INNER JOIN categories on commodities.category_id = categories.id  WHERE commodities.seller_id != ? AND commodities.category_id = ? AND commodities.buyer_id IS NULL", session['user_id'], category_id)
        except ValueError:
            flash("invalid category!")
            Commodities = db.execute("SELECT commodities.*, categories.name as category FROM commodities INNER JOIN categories on commodities.category_id = categories.id  WHERE commodities.seller_id != ? AND commodities.buyer_id IS NULL", session['user_id'])

    return render_template("buy.html",categories = categories, commodities = Commodities, buy_link ="active",category_id = category_id )


# details about specific commodity
@app.route('/commodity-details/<id>')
@login_required
def details(id):
    # retrieve all data about certain commodity using id
    Commodity = db.execute("SELECT commodities.*, categories.name as category , users.username as seller FROM commodities INNER JOIN categories on commodities.category_id = categories.id INNER JOIN users on commodities.seller_id = users.id WHERE commodities.id = ?", id)[0]
    # retrieve all bids for this commodity
    bids = db.execute("SELECT Auctions.*, users.username as bidder , users.id, users.imgURL FROM Auctions INNER JOIN users on Auctions.user_id = users.id WHERE Auctions.commodity_id = ? ", id)
    return render_template("details.html",Commodity = Commodity, bids = bids)

# user bids
@app.route('/bid', methods=["POST"])
@login_required
def bid():
    commodity_id = request.form.get("id")
    price = request.form.get("pirce")
    # if valid price and not less than minimum price
    try:
        price = float(price)
        min_price = db.execute("SELECT min_price FROM commodities WHERE id = ?", commodity_id)[0]
        print(min_price)
        if price < min_price['min_price']:
            flash("danger")
            flash(["Invalid Price"])
            return redirect(f'/commodity-details/{commodity_id}')
    except ValueError:
        flash("danger")
        flash(["Invalid Price"])
        return redirect(f'/commodity-details/{commodity_id}')

    # if user did not  bid before
    row = db.execute("SELECT * FROM Auctions WHERE commodity_id = ? AND user_id = ?", int(commodity_id), session['user_id'])
    if len(row) == 0:
        db.execute("INSERT INTO Auctions (commodity_id, user_id, price) VALUES (?, ?, ?)", int(commodity_id), session['user_id'], price)
        flash("success")
        flash(["added successfully!"])
        return redirect(f'/commodity-details/{commodity_id}')

    # if user already bid
    else:
        db.execute("UPDATE Auctions SET price = ? WHERE commodity_id = ? AND user_id = ?", price, int(commodity_id), session['user_id'])
        flash("success")
        flash(["updated successfully!"])
        return redirect(f'/commodity-details/{commodity_id}')

# delete user bid
@app.route('/delete-bid/<commodity_id>/<user_id>')
@login_required
def delete_bid(commodity_id, user_id):
    # check user identity
    commodity_id = int(commodity_id)
    user_id = int(user_id)
    if session['user_id'] == user_id:
        db.execute("DELETE FROM Auctions WHERE commodity_id = ? AND user_id = ?", commodity_id , user_id)
        flash('success')
        flash(["Deleted successfully!"])
        return redirect(f'/commodity-details/{commodity_id}')
    else:
        flash('danger')
        flash(["something wrong happened!"])
        return redirect(f'/commodity-details/{commodity_id}')


# seller choose user and sell item
@app.route('/sell-commodity', methods=["POST"])
@login_required
def sell_item():
    try:
        bid = json.loads(request.form.get("bid").replace("\'", "\""))
    except:
        flash('danger')
        flash(["something wrong happened!"])
        return redirect(f'/commodity-details/{id}')

    seller_id = int(request.form.get("seller_id"))
    if session['user_id'] == seller_id:
        # update db
        db.execute("UPDATE commodities SET price = ?, buyer_id = ?, bought_at = CURRENT_TIMESTAMP  WHERE id = ?", bid['price'], bid['user_id'], bid['commodity_id'])
        flash("success")
        flash(["Sold successfully!"])
        return redirect("/myCommodities")
    else:
        flash('danger')
        flash(["something wrong happened!"])
        return redirect(f'/commodity-details/{id}')


# show user and purchases
@app.route('/myPurchases')
@login_required
def myPurchases():
    # retrieve user commodities from db
    myPurchases = db.execute("SELECT commodities.*, categories.name as category FROM commodities INNER JOIN categories on commodities.category_id = categories.id  where commodities.buyer_id = ?", session['user_id'])
    return render_template("myPurchases.html", purchases= myPurchases, myPurchases_link ="active")

