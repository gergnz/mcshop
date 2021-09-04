import os
import json
import shutil
from urllib.request import urlretrieve
from flask import Blueprint, render_template, redirect, url_for, request, send_from_directory, jsonify
from flask_login import login_required, current_user
from flask_table import Table, Col, ButtonCol
import docker
import requests

main = Blueprint('main', __name__)

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
    return render_template('profile.html', name=current_user.name)

class ContainerTable(Table):
    status = Col('Status')
    image = Col('Image')
    name = Col('Name')
    delete = ButtonCol(
        'Delete',
        'main.containermgt',
        url_kwargs=dict(id='id'),
        url_kwargs_extra=dict(task='delete'),
        button_attrs={'class': 'btn btn-danger btn-sm'}
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
    classes = ['table', 'table-striped', 'table-bordered', 'bg-light']
    html_attrs = dict(cellspacing='0')
    table_id = 'allcontainers'

@main.route('/containers')
@login_required
def containers():
    client = docker.from_env()
    allcontainers = client.containers.list(all=True)

    table = ContainerTable(allcontainers)
    return render_template('containers.html', allcontainers=table.__html__(),)

@main.route('/containermgt', methods=['POST'])
@login_required
def containermgt():
    container_id = request.args.get('id')
    task = request.args.get('task')

    client = docker.from_env()

    cont = client.containers.get(container_id)

    if task == 'stop':
        cont.stop()
    if task == 'start':
        cont.start()
    if task == 'delete':
        cont.stop()
        cont.wait()
        cont.remove()

    return redirect(url_for('main.containers'))

@main.route('/serverjars', methods=['GET'])
@login_required
def serverjars():

    mc_versions_result = requests.get('https://launchermeta.mojang.com/mc/game/version_manifest.json')
    mc_versions = mc_versions_result.json()

    return render_template('serverjars.html', mc_versions=mc_versions)

@main.route('/mcuuid/<name>', methods=['GET'])
@login_required
def mcuuid(name):

    url = "https://api.mojang.com/users/profiles/minecraft/"+name
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json())
    return ('', 204)

@main.route('/newmcserver', methods=['POST'])
@login_required
def newmcserver(): #pylint: disable=too-many-locals

    opusers = request.form.get('opusers')
    whitelistusers = request.form.get('whitelistusers')
    newversion = request.form.get('version')
    servername = request.form.get('servername')

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
            tmp['uuid'] = tmp.pop('id')
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
            tmp['uuid'] = tmp.pop('id')
            whitelist.append(tmp)

    with open('minecraft/'+servername+'/whitelist.json', 'w', encoding='UTF-8') as file:
        json.dump(whitelist, file, indent=4, sort_keys=True)

    with open('minecraft/'+servername+'/eula.txt', 'w', encoding='ascii') as file:
        file.write('eula=true')

    return ''

class MinecraftTable(Table):
    name = Col('Name')
    delete = ButtonCol(
        'Delete',
        'main.minecraftmgt',
        url_kwargs=dict(name='name'),
        url_kwargs_extra=dict(task='delete'),
        button_attrs={'class': 'btn btn-danger btn-sm'}
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
@login_required
def minecrafts():

    allminecrafts=[]
    for item in os.listdir('minecraft'):
        allminecrafts.append({'name': item})

    table = MinecraftTable(allminecrafts)
    return render_template('minecrafts.html', allminecrafts=table.__html__(),)

@main.route('/minecraftmgt', methods=['POST'])
@login_required
def minecraftmgt():
    name = request.args.get('name')
    task = request.args.get('task')

    if task == 'delete':
        try:
            shutil.rmtree('minecraft/'+name)
        except OSError as error:
            print(f'Error: {name} : {error.strerror}')

    if task == 'run':
        client = docker.from_env()
        client.containers.run('nginx', detach=True, name=name)

    return redirect(url_for('main.minecrafts'))
