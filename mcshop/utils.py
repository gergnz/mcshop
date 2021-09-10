from functools import wraps
from flask import session, redirect, flash, url_for
from flask_login import login_required

def otp_required(func):
    @login_required
    @wraps(func)
    def wrapper(*args, **kwargs):
        if '_otp_verified' not in session or session['_otp_verified'] is False:
            flash("Please setup TOTP.", "info")
            return redirect(url_for('main.profile'))
        return func(*args, **kwargs)
    return wrapper
