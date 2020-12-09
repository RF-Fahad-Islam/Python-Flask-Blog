from datetime import datetime
import json
import os
import math

from flask import Flask, redirect, render_template, request, session
from flask_mail import Mail
# from flaskwebgui import FlaskUI
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

#TODO: Reading the config.json file for passing to all HTML pages
with open('config.json') as f:
    params = json.load(f)["params"]

local_server = params["local_server"] #True or False
app = Flask(__name__)
app.secret_key = "This_is_a_secret_key_127" #Set the secret key to use session
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT="465",
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail-user"],
    MAIL_PASSWORD=params["gmail-password"]
)
app.config["UPLOAD_FOLDER"] = params["upload_location"]
mail = Mail(app)

#TODO: Inserting uri of specified server
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["pd_uri"]

db = SQLAlchemy(app)
# ui = FlaskUI(app)

#TODO: Creating classes to insert one or get the database content
class Contacts(db.Model):
    """
    The contacts validate class and rows to add to the mysql database
    """
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=False, nullable=False)
    email = db.Column(db.String(20), unique=True, nullable=False)
    tel = db.Column(db.String(12), unique=True, nullable=False)
    message = db.Column(db.String(120), unique=False, nullable=False)

class Posts(db.Model):
    """
    Fetch all contents of posts table
    """
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(10), unique=False, nullable=False)
    tagline = db.Column(db.String(10), unique=False, nullable=False)
    slug = db.Column(db.String(20), unique=True, nullable=False)
    content = db.Column(db.String(), unique=True, nullable=False)
    img_file = db.Column(db.String(25), unique=False, nullable=False)
    date = db.Column(db.String(25), unique=True, nullable=True)
    

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    #[0: params['no_of_posts']]
    #posts = posts[]
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page= int(page)
    posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    #Pagination Logic
    #First
    if (page==1):
        prev = "#"
        next_ = "/?page="+ str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page - 1)
        next_ = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next_ = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next_=next_)

@app.route("/about")
def about():
    return render_template("about.html", params=params)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    tried = 0
    if "user" in session and session["user"] == params["admin_user"]:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)
        
    
    if request.method == "POST":
        loginDict = request.form
        username = loginDict.get("username")
        password = loginDict.get("password")
        isautosave = loginDict.get("isautosave")
        posts = Posts.query.all()
        if username == params["admin_user"] and password == params["admin_password"]:
            #Set the session variable
            if isautosave == "Yes":
                session["user"] = username
            return render_template("dashboard.html", params=params, posts=posts)
        else:
            tried += 1
    if tried < 4:
        return render_template("login.html", params=params)

@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    if "user" in session and session["user"] == params["admin_user"]:
        post = Posts.query.filter_by(sno=sno).first()
        if request.method == "POST":
            contentDict = request.form
            title = contentDict.get("title")
            tagline = contentDict.get("tagline")
            slug = contentDict.get("slug")
            img_file = contentDict.get("img_file")
            content = contentDict.get("content")
        
            if sno == "0":
                post = Posts(title=title,date=datetime.now(), tagline=tagline, slug=slug, img_file=img_file, content=content)
                db.session.add(post)
                db.session.commit()
                return redirect("/dashboard")
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.tagline = tagline
                post.slug = slug
                post.img_file = img_file
                post.content = content
                db.session.commit()
                return redirect("/edit/"+sno)
        return render_template("edit.html", params=params,post=post, sno=sno)
    return render_template("login.html")

@app.route("/uploader", methods=["GET", "POST"])
def uploader():
    if "user" in session and session["user"] == params["admin_user"]:
        if request.method == "POST":
            f = request.files['file1']
            f.save(os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(f.filename)))
            return render_template("upload.html", filename=f.filename)
            
@app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/dashboard")

@app.route("/delete/<string:sno>")
def delete(sno):
    post = Posts.query.filter_by(sno=sno).first()
    db.session.delete(post)
    db.session.commit()    
    return redirect("/dashboard")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        contactDict = request.form
        name = contactDict.get("name")
        email = contactDict.get("email")
        tel = contactDict.get("tel")
        message = contactDict.get("message")
        entry = Contacts(name=name, email=email, tel=tel,
                         message=message)  # Creating the entry
        db.session.add(entry)  # Enter the entry to the dataset
        db.session.commit()
        mail.send_message(f"New message from the {params['blog_title']} by {name} (email => {email})",
                          sender=email, recipients=[params['send_to']],
                          body=f"----------------Details of the User----------------\n\nName : {name}\nEmail : {email}\nTelephone Number : {tel}\nMessage : {message}")

    return render_template("contact.html", params=params)

@app.route("/post/<string:post_slug>", methods=["GET"])
def post(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)


if __name__ == "__main__":
    app.run(debug=True)
