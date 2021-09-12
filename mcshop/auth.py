from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required
import pyotp
from .models import User

auth = Blueprint('auth', __name__)

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

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))

    session['_otp_verified'] = False
    if otp == "":
        flash('Please setup TOTP.', 'info')
        login_user(user, remember=remember_me)
        return redirect(url_for('profile.profilepage'))

    if pyotp.TOTP(user.totptoken).verify(otp):
        session['_otp_verified'] = True
    else:
        flash('TOTP Check Failed. Please check your login details and try again.')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember_me)
    return redirect(url_for('minecraft.minecrafts'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
