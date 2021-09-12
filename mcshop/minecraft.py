import os
import json
import uuid
import shutil
import requests
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_table import Table, Col, ButtonCol, LinkCol
import docker
from .utils import otp_required, ModalCol

minecraft = Blueprint('minecraft', __name__)

class MinecraftTable(Table):
    name = Col('Name')
    delete = ModalCol(
        'Delete',
        'minecraft.minecraftmgt',
        url_kwargs=dict(name='name'),
        url_kwargs_extra=dict(task='delete'),
        button_attrs={'class': 'btn btn-danger btn-sm', 'data-bs-toggle': 'modal', 'data-bs-target': '#deleteModal'}
    )
    run = ButtonCol(
        'Run',
        'minecraft.minecraftmgt',
        url_kwargs=dict(name='name'),
        url_kwargs_extra=dict(task='run'),
        button_attrs={'class': 'btn btn-primary btn-sm'}
    )
    edit = LinkCol(
        'Edit',
        'minecraft.mcedit',
        url_kwargs=dict(mcname='name')
    )
    classes = ['table', 'table-striped', 'table-bordered', 'bg-light']
    html_attrs = dict(cellspacing='0')
    table_id = 'allminecrafts'

@minecraft.route('/minecrafts', methods=['GET'])
@otp_required
def minecrafts():

    allminecrafts=[]
    for item in os.listdir('minecraft'):
        if item.startswith('.'):
            continue
        allminecrafts.append({'name': item})

    table = MinecraftTable(allminecrafts)
    return render_template('minecrafts.html', allminecrafts=table.__html__(),)

@minecraft.route('/minecraftmgt', methods=['POST'])
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

    return redirect(url_for('minecraft.minecrafts'))

@minecraft.route("/mcedit/<mcname>", methods=['GET'])
@otp_required
def mcedit(mcname):
    with open('minecraft/'+mcname+'/ops.json', 'r', encoding='UTF-8') as file:
        opusers = json.load(file)
    with open('minecraft/'+mcname+'/whitelist.json', 'r', encoding='UTF-8') as file:
        whitelist = json.load(file)
    with open('minecraft/'+mcname+'/mc.json', 'r', encoding='UTF-8') as file:
        mcsettings = json.load(file)
    with open('minecraft/'+mcname+'/server.properties', 'r', encoding='UTF-8') as file:
        server_props = file.read()

    return render_template('mcedit.html',
        mcname=mcname,
        opusers=opusers,
        whitelist=whitelist,
        mcsettings=mcsettings,
        server_props=server_props
    )

@minecraft.route("/mcsave", methods=["POST"])
@otp_required
def mcsave(): #pylint: disable=too-many-locals,too-many-statements

    try:
        opusers = request.form.get('opusers')
        whitelistusers = request.form.get('whitelistusers')
        mcname = request.form.get('mcname')
        server_props = request.form.get('server_props')

        print(mcname)

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

        with open('minecraft/'+mcname+'/ops.json', 'w', encoding='UTF-8') as file:
            json.dump(opslist, file, indent=4, sort_keys=True)

        whitelist=[]
        for user in whitelistusers.split(','):
            url = "https://api.mojang.com/users/profiles/minecraft/"+user
            response = requests.get(url)
            if response.status_code == 200:
                tmp = response.json()
                tmp['uuid'] = str(uuid.UUID(tmp.pop('id')))
                whitelist.append(tmp)

        with open('minecraft/'+mcname+'/whitelist.json', 'w', encoding='UTF-8') as file:
            json.dump(whitelist, file, indent=4, sort_keys=True)

        with open('minecraft/'+mcname+'/server.properties', 'w', encoding='ascii') as file:
            file.write(server_props)

        return ''
    except Exception as error: #pylint: disable=broad-except
        return (jsonify({'Error': str(error)}), 500)
