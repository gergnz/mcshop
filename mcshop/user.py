from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort
from werkzeug.security import generate_password_hash
from flask_table import Table, Col, BoolCol
from .utils import otp_required, UserModalCol
from .models import User
from . import db

user = Blueprint('user', __name__)

class UserTable(Table):
    name = Col('Name')
    email = Col('Email')
    useradmin = BoolCol('User Administrator')
    delete = UserModalCol(
        'Delete',
        'user.deluser',
        url_kwargs=dict(id='id'),
        button_attrs={'class': 'btn btn-danger btn-sm', 'data-bs-toggle': 'modal', 'data-bs-target': '#deleteModal'}
    )
    classes = ['table', 'table-striped', 'table-bordered', 'bg-light']
    html_attrs = dict(cellspacing='0')
    table_id = 'allusers'

@user.route('/users', methods=['GET'])
@otp_required
def users():
    if not session['useradmin']:
        abort(403)
    allusers = User.query.all()

    table = UserTable(allusers)
    return render_template('users.html', allusers=table.__html__(),)

@user.route('/deluser', methods=['POST'])
@otp_required
def deluser():
    user_id = request.args.get('id')
    localuser = User.query.filter_by(id=user_id).first()

    if not localuser:
        flash("The craziest thing happened, the user doesn't exist!")
        return redirect(url_for('user.users'))

    db.session.delete(localuser) #pylint: disable=no-member
    db.session.commit() #pylint: disable=no-member

    return redirect(url_for('user.users'))

@user.route('/adduser', methods=['POST'])
@otp_required
def adduser():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('newpwone')
    useradmin = bool(request.form.get('useradmin'))

    localuser = User.query.filter_by(email=email).first()

    if localuser:
        flash('Email address already exists')
        return redirect(url_for('user.users'))

    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'), useradmin=useradmin)

    db.session.add(new_user) #pylint: disable=no-member
    db.session.commit() #pylint: disable=no-member

    return redirect(url_for('user.users'))
