from flask import Blueprint
from flask import request
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from app.models import User

user = Blueprint("user", __name__)


@user.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return {"message": "Username and password required"}, 400

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        return {"message": "Login successful"}, 200
    return {"message": "Invalid username or password"}, 401


@user.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    print(name, email, password)
    if not name or not email or not password:
        return {"message": "Name, Email and password required"}, 400

    if User.query.filter_by(email=email).first():
        return {"message": "Username already exists"}, 409

    hashed_password = generate_password_hash(password)
    new_user = User(name=name, password=hashed_password, email=email)
    db.session.add(new_user)
    db.session.commit()
    return {"message": "Registration successful"}, 201
