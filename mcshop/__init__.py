#pylint: disable=import-outside-toplevel
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_talisman import Talisman
from flask_seasurf import SeaSurf

db = SQLAlchemy()
csrf = SeaSurf()

def create_app():
    app = Flask(__name__)

    csrf.init_app(app)

    csp = {
        'default-src': '\'self\'',
        'img-src': [
            '\'self\'',
            'data:'
        ],
        'script-src': [
            '\'self\'',
            'https://cdn.jsdelivr.net'
        ],
        'font-src': 'https://cdn.jsdelivr.net',
        'style-src': [
            'https://cdn.jsdelivr.net',
            '\'sha256-pSbjG217o7W/VwmF9vxu3sCO3CMsdtsdAX54YrPw3rg=\'',
            '\'sha256-biLFinpqYMtWHmXfkA1BPeCY0/fNt46SAZ+BBk5YUog=\'',
            '\'unsafe-hashes\''
        ]
    }

    permissions_policy={}

    Talisman(app, content_security_policy=csp, permissions_policy=permissions_policy)

    app.config['SECRET_KEY'] = 'E65983E0-3AB3-420F-BAE8-0CCF19B3CF0D'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = "strong"
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .user import user as user_blueprint
    app.register_blueprint(user_blueprint)

    from .profile import profile as profile_blueprint
    app.register_blueprint(profile_blueprint)

    from .container import container as container_blueprint
    app.register_blueprint(container_blueprint)

    from .minecraft import minecraft as minecraft_blueprint
    app.register_blueprint(minecraft_blueprint)

    from .new import new as new_blueprint
    app.register_blueprint(new_blueprint)

    from .advanced import advanced as advanced_blueprint
    app.register_blueprint(advanced_blueprint)

    return app
