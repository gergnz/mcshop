from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask_table import Table, Col, ButtonCol
from .models import User
from . import db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember_me = True if request.form.get('rememberMe') else False

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember_me)
    return redirect(url_for('main.profile'))

@auth.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

class UserTable(Table):
    name = Col('Name')
    email = Col('Email')
    delete = ButtonCol('Delete', 'auth.deluser', url_kwargs=dict(id='id'), button_attrs={'class': 'btn btn-danger btn-sm'})
    classes = ['table', 'table-striped', 'table-bordered', 'bg-light']
    html_attrs = dict(cellspacing='0')
    table_id = 'allusers'

@auth.route('/users', methods=['GET'])
@login_required
def users():
    allusers = User.query.all()

    # Populate the table
    table = UserTable(allusers)
    return render_template('users.html', allusers=table.__html__(),)

@auth.route('/deluser', methods=['POST'])
@login_required
def deluser():
    user_id = request.args.get('id')
    user = User.query.filter_by(id=user_id).first()

    if not user:
        flash("The craziest thing happened, the user doesn't exist!")
        return redirect(url_for('auth.users'))

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('auth.users'))


@auth.route('/adduser', methods=['POST'])
@login_required
def adduser():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('auth.users'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.users'))
