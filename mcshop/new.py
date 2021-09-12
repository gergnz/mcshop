import os
import json
import uuid
from urllib.request import urlretrieve
from flask import Blueprint, render_template, request, jsonify
import requests
from .utils import otp_required
from .mcfiles import start_sh, server_props

new = Blueprint('new', __name__)

@new.route('/newserver', methods=['GET'])
@otp_required
def newserver():

    mc_versions_result = requests.get('https://launchermeta.mojang.com/mc/game/version_manifest.json')
    mc_versions = mc_versions_result.json()

    return render_template('newserver.html', mc_versions=mc_versions)

@new.route('/newmcserver', methods=['POST'])
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
