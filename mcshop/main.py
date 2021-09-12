import os
from flask import Blueprint, render_template, send_from_directory, jsonify
import requests
from .utils import otp_required

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

@main.route('/mcuuid/<name>', methods=['GET'])
@otp_required
def mcuuid(name):

    url = "https://api.mojang.com/users/profiles/minecraft/"+name
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify(response.json())
    return ('', 204)
