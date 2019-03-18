from app.app import Flask
from app.libs.redis_queue import RedisQueue
from app.models.base import db
from flask_cors import CORS

redis_queue = RedisQueue()


def register_blueprints(app):
    from app.api.v1 import create_blueprint_v1
    app.register_blueprint(create_blueprint_v1(), url_prefix='/v1')


def register_plugin(app):
    from app.models.base import db
    with app.app_context():
        db.init_app(app)
        db.create_all()


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.setting")
    app.config.from_object("app.config.secure")

    register_blueprints(app)
    register_plugin(app)

    CORS(app)
    return app

