from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import json

with open("config.json") as f:
    params = json.load(f)["params"]
local_server = params["local_server"]
app = Flask(__name__)
app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = "465",
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params["gmail-user"],
    MAIL_PASSWORD = params["gmail-password"]
)
if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
    
db = SQLAlchemy(app)

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=False, nullable=False)
    email = db.Column(db.String(20), unique=True, nullable=False)
    tel = db.Column(db.String(14), unique=True, nullable=False)
    message = db.Column(db.String(120), unique=True, nullable=False)

mail = Mail(app)
@app.route("/")
def home():
    return render_template("index.html", params=params)

@app.route("/about")
def about():
    return render_template("about.html", params=params)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        contactDict = request.form
        name = contactDict.get("name")
        email = contactDict.get("email")
        tel = contactDict.get("tel")
        message = contactDict.get("message")
        entry = Contact(name=name, email=email, tel=tel, message=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message(f"Conding Thunder! New Message by \"{name}\"",
                          sender=email, recipients=[params["sent_to"]],
                          body=f"Name : {name}\nEmail : {email}\nPhone Number : {tel}\nMessage : {message}")
    return render_template("contact.html", params=params)

@app.route("/post/<string:post_slug>", methods=["GET"])
def post(post_slug):
    return render_template("post.html", params=params)

if __name__ == "__main__":
    app.run(debug=True)