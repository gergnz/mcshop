from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_user, logout_user, login_required
from flask_table import Table, Col, ButtonCol
from flask_table.html import element
import pyotp
from .utils import otp_required
from .models import User
from . import db

auth = Blueprint('auth', __name__)

class ModalCol(ButtonCol):
    def td_contents(self, item, attr_list):
        button_attrs = dict(self.button_attrs)
        button_attrs['data-href']=self.url(item)
        if item.id == current_user.id:
            button_attrs['disabled']=True
        button = element(
            'button',
            attrs=button_attrs,
            content=self.text(item, attr_list),
        )
        return button

@auth.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember_me = bool(request.form.get('rememberMe'))
    otp = request.form.get('otp')

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page

    session['_otp_verified'] = False
    if otp == "":
        flash('Please setup TOTP.', 'info')
        login_user(user, remember=remember_me)
        return redirect(url_for('main.profile'))

    if pyotp.TOTP(user.totptoken).verify(otp):
        session['_otp_verified'] = True
    else:
        flash('TOTP Check Failed. Please check your login details and try again.')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember_me)
    return redirect(url_for('main.minecrafts'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

class UserTable(Table):
    name = Col('Name')
    email = Col('Email')
    delete = ModalCol(
        'Delete',
        'auth.deluser',
        url_kwargs=dict(id='id'),
        button_attrs={'class': 'btn btn-danger btn-sm', 'data-bs-toggle': 'modal', 'data-bs-target': '#deleteModal'}
    )
    classes = ['table', 'table-striped', 'table-bordered', 'bg-light']
    html_attrs = dict(cellspacing='0')
    table_id = 'allusers'

@auth.route('/users', methods=['GET'])
@otp_required
def users():
    allusers = User.query.all()

    # Populate the table
    table = UserTable(allusers)
    return render_template('users.html', allusers=table.__html__(),)

@auth.route('/deluser', methods=['POST'])
@otp_required
def deluser():
    user_id = request.args.get('id')
    user = User.query.filter_by(id=user_id).first()

    if not user:
        flash("The craziest thing happened, the user doesn't exist!")
        return redirect(url_for('auth.users'))

    db.session.delete(user) #pylint: disable=no-member
    db.session.commit() #pylint: disable=no-member

    return redirect(url_for('auth.users'))


@auth.route('/adduser', methods=['POST'])
@otp_required
def adduser():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('newpwone')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('auth.users'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user) #pylint: disable=no-member
    db.session.commit() #pylint: disable=no-member

    return redirect(url_for('auth.users'))
