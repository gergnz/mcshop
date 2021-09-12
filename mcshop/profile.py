from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user, logout_user
import pyotp
from .models import User
from . import db

profile = Blueprint('profile', __name__)

@profile.route('/profile')
@login_required
def profilepage():
    return render_template('profile.html', name=current_user.name, email=current_user.email)

@profile.route("/token", methods=["GET"])
@login_required
def token():
    totptoken = pyotp.random_base32()
    user = User.query.filter_by(id=current_user.id).first()
    user.totptoken = totptoken
    db.session.commit() #pylint: disable=no-member
    return jsonify({'SecretCode': totptoken})

@profile.route("/token", methods=["POST"])
@login_required
def checktoken():
    usercode = request.form.get('usercode')
    user = User.query.filter_by(id=current_user.id).first()
    if pyotp.TOTP(user.totptoken).verify(usercode):
        # inform users if OTP is valid
        flash("The TOTP 2FA token has been saved.", "success")
        logout_user()
        return redirect(url_for('auth.login'))

    flash("You have supplied an invalid 2FA token!", "danger")
    return redirect(url_for('profile.profilepage'))

@profile.route("/changepassword", methods=["POST"])
@login_required
def changepassword():
    existing = request.form.get('existing')
    newpwone = request.form.get('newpwone')
    newpwtwo = request.form.get('newpwtwo')

    if newpwone != newpwtwo:
        flash("Passwords don't match. Please check your passwords!", "danger")
        return redirect(url_for('profile.profilepage'))

    user = User.query.filter_by(id=current_user.id).first()

    print(existing)
    print(user.password)
    if not user or not check_password_hash(user.password, existing):
        flash('Please check your login details and try again.', "danger")
        return redirect(url_for('profile.profilepage'))

    user.password = generate_password_hash(newpwone, method='sha256')
    db.session.commit() #pylint: disable=no-member

    flash('Password changed successfully.', "success")
    return redirect(url_for('profile.profilepage'))
