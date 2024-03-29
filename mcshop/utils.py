from functools import wraps
from flask import session, redirect, flash, url_for
from flask_login import login_required, current_user
from flask_table.html import element
from flask_table import ButtonCol

def otp_required(func):
    @login_required
    @wraps(func)
    def wrapper(*args, **kwargs):
        if '_otp_verified' not in session or session['_otp_verified'] is False:
            flash("Please setup TOTP.", "info")
            return redirect(url_for('profile.profilepage'))
        return func(*args, **kwargs)
    return wrapper

class ModalCol(ButtonCol):
    def td_contents(self, item, attr_list):
        button_attrs = dict(self.button_attrs)
        button_attrs['data-href']=self.url(item)
        button = element(
            'button',
            attrs=button_attrs,
            content=self.text(item, attr_list),
        )
        return button

class UserModalCol(ButtonCol):
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

class Modal2Col(ButtonCol):
    def td_contents(self, item, attr_list):
        button_attrs = dict(self.button_attrs)
        forge = button_attrs.pop('forge', '')
        button_attrs['data-href']=self.url_kwargs(item)['id']+forge
        button = element(
            'button',
            attrs=button_attrs,
            content=self.text(item, attr_list),
        )
        return button

class FileButtonCol(ButtonCol):
    def td_contents(self, item, attr_list):
        button_attrs = dict(self.button_attrs)
        unzip = button_attrs.pop('unzip', False)
        run = button_attrs.pop('run', False)
        task = ''
        if unzip:
            task = 'unzip'
        elif run:
            task = 'run'
        button_attrs['class']=button_attrs['class']+' uploadFile'+task
        button_attrs['data-item']=item['name']
        button_attrs['data-task']=task
        button = element(
            'button',
            attrs=button_attrs,
            content=self.text(item, attr_list),
        )
        return button
