import os
import json
import shutil
import zipfile
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, _app_ctx_stack
from werkzeug.utils import secure_filename
from flask_table import Table, Col
import docker
from .utils import otp_required, FileButtonCol, Modal2Col

ALLOWED_EXTENSIONS = {'jar', 'zip'}

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
        uploadrun = FileButtonCol(
            'Upload & Run',
            'advanced.upload_file',
            button_attrs={'class': 'btn btn-primary btn-sm', 'run': True}
        )
        logs = Modal2Col(
            'Logs',
            '',
            url_kwargs=dict(id='name'),
            button_attrs={'class': 'btn btn-secondary btn-sm', 'data-bs-toggle': 'modal', 'data-bs-target': '#logsModal', 'forge': '-forge'}
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
    task = request.form.get('task')
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
        if task == 'unzip':
            with zipfile.ZipFile('minecraft/'+mcname+'/'+filename, mode="r") as archive:
                for file in archive.namelist():
                    archive.extract(file, 'minecraft/'+mcname+'/')
        if task == 'run':
            minecraft_home = os.environ.get('MC_HOME')
            # change the start file to use the run.sh from forge
            with open('minecraft/'+mcname+"/start.sh", 'r', encoding='ascii') as a_file:
                list_of_lines = a_file.readlines()
                for idx, line in enumerate(list_of_lines):
                    if line.startswith('java'):
                        list_of_lines[idx] = "#"+line
                list_of_lines.append("./run.sh")
                a_file.close()
            with open('minecraft/'+mcname+"/start.sh", "w", encoding='ascii') as a_file:
                a_file.writelines(list_of_lines)
                a_file.close()
            # run the forge installer
            with open('minecraft/'+mcname+'/mc.json', "r", encoding='UTF-8') as mc_file:
                mc_vars = json.load(mc_file)
            client = docker.from_env()
            client.containers.run(
                mc_vars['serverrunner'],
                'java -jar /app/'+filename+' --installServer /app',
                detach=True,
                volumes=[minecraft_home+'/'+mcname+':/app'],
                name=mcname+'-forge'
            )
    else:
        return 'Unallowed file type.', 400
    return 'OK', 201
