import os
import json
import shutil
import uuid
from urllib.request import urlretrieve
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, redirect, url_for, request, send_from_directory, jsonify, flash, Response
from flask_login import login_required, current_user, logout_user
from flask_table import Table, Col, ButtonCol
from flask_table.html import element
import pyotp
import docker
import requests
from .utils import otp_required
from .models import User
from . import db
from .mcfiles import start_sh, server_props

main = Blueprint('main', __name__)

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

class Modal2Col(ButtonCol):
    def td_contents(self, item, attr_list):
        button_attrs = dict(self.button_attrs)
        button_attrs['data-href']=self.url_kwargs(item)['id']
        button = element(
            'button',
            attrs=button_attrs,
            content=self.text(item, attr_list),
        )
        return button

@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(main.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name, email=current_user.email)

class ContainerTable(Table):
    status = Col('Status')
    image = Col('Image')
    name = Col('Name')
    delete = ModalCol(
        'Delete',
        'main.containermgt',
        url_kwargs=dict(id='id'),
        url_kwargs_extra=dict(task='delete'),
        button_attrs={'class': 'btn btn-danger btn-sm', 'data-bs-toggle': 'modal', 'data-bs-target': '#deleteModal'}
    )
    stop = ButtonCol(
        'Stop',
        'main.containermgt',
        url_kwargs=dict(id='id'),
        url_kwargs_extra=dict(task='stop'),
        button_attrs={'class': 'btn btn-warning btn-sm'}
    )
    start = ButtonCol(
        'Start',
        'main.containermgt',
        url_kwargs=dict(id='id'),
        url_kwargs_extra=dict(task='start'),
        button_attrs={'class': 'btn btn-success btn-sm'}
    )
    logs = Modal2Col(
        'Logs',
        '',
        url_kwargs=dict(id='id'),
        button_attrs={'class': 'btn btn-secondary btn-sm', 'data-bs-toggle': 'modal', 'data-bs-target': '#logsModal'}
    )
    classes = ['table', 'table-striped', 'table-bordered', 'bg-light']
    html_attrs = dict(cellspacing='0')
    table_id = 'allcontainers'

@main.route('/containers')
@otp_required
def containers():
    client = docker.from_env()
    allcontainers = client.containers.list(all=True)

    table = ContainerTable(allcontainers)
    return render_template('containers.html', allcontainers=table.__html__(),)

@main.route('/containermgt', methods=['POST'])
@otp_required
def containermgt():
    container_id = request.args.get('id')
    task = request.args.get('task')

    client = docker.from_env()

    cont = client.containers.get(container_id)

    try:
        if task == 'stop':
            cont.stop()
            flash("Container stopped successfully.", "success")
        if task == 'start':
            cont.start()
            flash("Container started successfully.", "success")
        if task == 'delete':
            cont.stop()
            cont.wait()
            cont.remove()
            flash("Container deleted successfully.", "success")
    except Exception as error: #pylint: disable=broad-except
        flash(f"Container operation failed: {error}", "danger")

    return redirect(url_for('main.containers'))

@main.route('/newserver', methods=['GET'])
@otp_required
def newserver():

    mc_versions_result = requests.get('https://launchermeta.mojang.com/mc/game/version_manifest.json')
    mc_versions = mc_versions_result.json()

    return render_template('newserver.html', mc_versions=mc_versions)

@main.route('/mcuuid/<name>', methods=['GET'])
@otp_required
def mcuuid(name):

    url = "https://api.mojang.com/users/profiles/minecraft/"+name
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json())
    return ('', 204)

@main.route('/newmcserver', methods=['POST'])
@otp_required
def newmcserver(): #pylint: disable=too-many-locals,too-many-statements

    try:
        opusers = request.form.get('opusers')
        whitelistusers = request.form.get('whitelistusers')
        newversion = request.form.get('version')
        servername = request.form.get('servername')
        serverrunner = request.form.get('serverrunner')
        port = request.form.get('port')
        gamemode = request.form.get('gamemode')

        os.mkdir('minecraft/'+servername)

        mc_versions_result = requests.get('https://launchermeta.mojang.com/mc/game/version_manifest.json')

        mc_versions = mc_versions_result.json()

        for version in mc_versions['versions']:
            if version['id'] == newversion:
                package_url = version['url']
                break

        package_result = requests.get(package_url)

        package_details = package_result.json()

        server_url = package_details['downloads']['server']['url']

        dst = 'minecraft/'+servername+'/server.jar'
        urlretrieve(server_url, dst)

        opslist=[]
        for user in opusers.split(','):
            url = "https://api.mojang.com/users/profiles/minecraft/"+user
            response = requests.get(url)
            if response.status_code == 200:
                tmp = response.json()
                tmp['uuid'] = str(uuid.UUID(tmp.pop('id')))
                tmp['level'] = 4
                tmp['bypassesPlayerLimit'] = False
                opslist.append(tmp)

        with open('minecraft/'+servername+'/ops.json', 'w', encoding='UTF-8') as file:
            json.dump(opslist, file, indent=4, sort_keys=True)

        whitelist=[]
        for user in whitelistusers.split(','):
            url = "https://api.mojang.com/users/profiles/minecraft/"+user
            response = requests.get(url)
            if response.status_code == 200:
                tmp = response.json()
                tmp['uuid'] = str(uuid.UUID(tmp.pop('id')))
                whitelist.append(tmp)

        with open('minecraft/'+servername+'/whitelist.json', 'w', encoding='UTF-8') as file:
            json.dump(whitelist, file, indent=4, sort_keys=True)

        with open('minecraft/'+servername+'/eula.txt', 'w', encoding='ascii') as file:
            file.write('eula=true')

        with open('minecraft/'+servername+'/start.sh', 'w', encoding='ascii') as file:
            file.write(start_sh)

        os.chmod('minecraft/'+servername+'/start.sh', 0o755)

        server_props_final = server_props.replace('PORT', port).replace('GAMEMODE', gamemode).replace('NAME', servername)

        with open('minecraft/'+servername+'/server.properties', 'w', encoding='ascii') as file:
            file.write(server_props_final)

        with open('minecraft/'+servername+'/mc.json', 'w', encoding='ascii') as file:
            json.dump({'serverrunner': serverrunner, 'port': port}, file, indent=4, sort_keys=True)

        return ''
    except Exception as error: #pylint: disable=broad-except
        return (jsonify({'Error': str(error)}), 500)

class MinecraftTable(Table):
    name = Col('Name')
    delete = ModalCol(
        'Delete',
        'main.minecraftmgt',
        url_kwargs=dict(name='name'),
        url_kwargs_extra=dict(task='delete'),
        button_attrs={'class': 'btn btn-danger btn-sm', 'data-bs-toggle': 'modal', 'data-bs-target': '#deleteModal'}
    )
    run = ButtonCol(
        'Run',
        'main.minecraftmgt',
        url_kwargs=dict(name='name'),
        url_kwargs_extra=dict(task='run'),
        button_attrs={'class': 'btn btn-primary btn-sm'}
    )
    classes = ['table', 'table-striped', 'table-bordered', 'bg-light']
    html_attrs = dict(cellspacing='0')
    table_id = 'allminecrafts'

@main.route('/minecrafts', methods=['GET'])
@otp_required
def minecrafts():

    allminecrafts=[]
    for item in os.listdir('minecraft'):
        if item.startswith('.'):
            continue
        allminecrafts.append({'name': item})

    table = MinecraftTable(allminecrafts)
    return render_template('minecrafts.html', allminecrafts=table.__html__(),)

@main.route('/minecraftmgt', methods=['POST'])
@otp_required
def minecraftmgt():
    name = request.args.get('name')
    task = request.args.get('task')

    if task == 'delete':
        try:
            shutil.rmtree('minecraft/'+name)
        except OSError as error:
            print(f'Error: {name} : {error.strerror}')

    if task == 'run':
        try:
            bind_ip = os.environ.get('BIND_IP')
            minecraft_home = os.environ.get('MC_HOME')
            with open('minecraft/'+name+'/mc.json', "r", encoding='UTF-8') as mc_file:
                mc_vars = json.load(mc_file)
            client = docker.from_env()
            client.containers.run(
                mc_vars['serverrunner'],
                '/app/start.sh',
                detach=True,
                restart_policy={"Name": "always"},
                ports={mc_vars['port']+'/tcp': (bind_ip, mc_vars['port'])},
                volumes=[minecraft_home+'/'+name+':/app'],
                name=name
            )
            flash("Container is running.", "success")
        except docker.errors.APIError as error:
            flash(f"Failed to run docker: {error}.", "danger")

    return redirect(url_for('main.minecrafts'))

def flask_logger(containerid):
    """creates logging information"""
    client = docker.from_env()
    cont = client.containers.get(containerid)
    for i in cont.logs(stream=True, tail=30):
        yield i

@main.route("/log_stream/<containerid>", methods=["GET"])
@otp_required
def stream(containerid):
    """returns logging information"""
    return Response(flask_logger(containerid), mimetype="text/plain", content_type="text/event-stream")

@main.route("/token", methods=["GET"])
@login_required
def token():
    totptoken = pyotp.random_base32()
    user = User.query.filter_by(id=current_user.id).first()
    user.totptoken = totptoken
    db.session.commit() #pylint: disable=no-member
    return jsonify({'SecretCode': totptoken})

@main.route("/token", methods=["POST"])
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
    return redirect(url_for('main.profile'))

@main.route("/changepassword", methods=["POST"])
@login_required
def changepassword():
    existing = request.form.get('existing')
    newpwone = request.form.get('newpwone')
    newpwtwo = request.form.get('newpwtwo')

    if newpwone != newpwtwo:
        flash("Passwords don't match. Please check your passwords!", "danger")
        return redirect(url_for('main.profile'))

    user = User.query.filter_by(id=current_user.id).first()

    print(existing)
    print(user.password)
    if not user or not check_password_hash(user.password, existing):
        flash('Please check your login details and try again.', "danger")
        return redirect(url_for('main.profile'))

    user.password = generate_password_hash(newpwone, method='sha256')
    db.session.commit() #pylint: disable=no-member

    flash('Password changed successfully.', "success")
    return redirect(url_for('main.profile'))
