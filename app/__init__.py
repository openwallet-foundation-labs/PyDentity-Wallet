from flask import (
    Flask,
    jsonify,
    render_template,
)
from flask_cors import CORS
from flask_qrcode import QRcode
from flask_session import Session

from config import Config
from app.handlers.errors import bp as errors_bp
from app.routes.main import bp as main_bp
from app.routes.auth import bp as auth_bp
import json


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.route("/manifest.json")
    @app.route("/manifest.webmanifest")
    def manifest():
        manifest_content = json.loads(
            render_template(
                "manifest.jinja", app_url=Config.APP_URL, app_name=Config.APP_NAME
            )
        )
        return jsonify(manifest_content)

    @app.route("/install")
    def install():
        return render_template(
            "pages/install.jinja",
            app_url=Config.APP_URL,
            app_name=Config.APP_NAME,
            project_url=Config.PROJECT_URL,
        )

    CORS(app)
    QRcode(app)
    Session(app)

    app.register_blueprint(errors_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app
