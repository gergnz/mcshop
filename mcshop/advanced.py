import os
import json
import uuid
import shutil
import zipfile
from pathlib import Path
import requests
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, _app_ctx_stack
from werkzeug.utils import secure_filename
from flask_table import Table, Col, ButtonCol, LinkCol
import docker
from .utils import otp_required, FileButtonCol

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'zip'}

advanced = Blueprint('advanced', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@advanced.route('/advanced', methods=['GET'])
@otp_required
def advance():

    allminecrafts=[]
    for item in os.listdir('minecraft'):
        if item.startswith('.'):
            continue
        allminecrafts.append({'name': item})

    class MinecraftTable(Table):

        name = Col('Name')
        file = FileButtonCol(
            'Upload',
            'advanced.upload_file',
            button_attrs={'class': 'btn btn-danger btn-sm'}
        )
        uploadunzip = FileButtonCol(
            'Upload & Unzip',
            'advanced.upload_file',
            button_attrs={'class': 'btn btn-primary btn-sm', 'unzip': True}
        )
        classes = ['table', 'table-striped', 'table-bordered', 'bg-light']
        html_attrs = dict(cellspacing='0')
        table_id = 'allminecrafts'
    table = MinecraftTable(allminecrafts)
    stat = shutil.disk_usage('minecraft')
    return render_template('advanced.html', allminecrafts=table.__html__(), stat=stat)

@advanced.route('/upload', methods=['POST'])
@otp_required
def upload_file():
    mcname = request.form.get('mcname')
    print(mcname)
    unzip = request.form.get('unzip')
    print(unzip)
    # check if the post request has the file part
    if 'file' not in request.files:
        return 'No filename supplied', 400
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return 'Filename empty', 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join('minecraft/'+mcname+'/', filename))
        if bool(unzip):
            with zipfile.ZipFile('minecraft/'+mcname+'/'+filename, mode="r") as archive:
                for file in archive.namelist():
                    archive.extract(file, 'minecraft/'+mcname+'/')
    else:
        return 'Unallowed file type.', 400
    return 'OK', 201
