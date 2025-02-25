import traceback

from flask import Flask, request, jsonify

import logging
import yaml

from logger import Logger
from routes import conference_booking_route
from auth_manager import auth_route
from flask_smorest import Api

from utils.exceptions import ValidationException, ApplicationException
from utils.registry import _registry

app = Flask(__name__)


app_logger = None

def setup_logging(app_name, log_level):
    """
    Initially `app_logger` is None

    This method initialises `app_logger` to a valid `logging.Logger` with the help of `siai.logging.Logger`

    :param app_name: The name of the application ex: tsdb-apm
    :param log_level: The log level. Could be based on environment variable. ex: INFO
    :return: logging.Logger instance
    """
    global app_logger
    app_logger = Logger(logger_name=app_name, min_level=log_level, format_verbose=True).logger
    return app_logger


# def load_config():
#     import os
#     print("os.getcwd():", os.getcwd())
#     config_file = '/app/configs/config.yaml'
#     with open(config_file, 'r') as f:
#         configs = yaml.safe_load(f)
#     return configs



def initialise_api_docs(app):
    app.config['OPENAPI_VERSION'] = '3.0.2'
    app.config['API_TITLE'] = 'conference API Server'
    app.config['API_VERSION'] = '0.0.8'


def set_routes(app):
    api = Api(app)
    api.register_blueprint(conference_booking_route)
    api.register_blueprint(auth_route)

def initialise_app_context():
    _registry.replace('app_logger', app_logger)

@app.errorhandler(Exception)
def handle_error(e):
    app_logger.error(traceback.format_exc())
    status_code = 500
    msg = "Server Error"
    reason = ''
    if isinstance(e, ValidationException):
        status_code = 400
        msg = e.message
    if isinstance(e, ApplicationException):
        msg = e.message
        status_code = 400
    if isinstance(e, ValueError):
        msg = str(e)
        status_code = 400

    err_msg = {"status_code": status_code, "msg": msg}
    return jsonify(err_msg), status_code

def list_routes(app):
    for rule in app.url_map.iter_rules():
        app_logger.info(rule)


def initialise(app):
    app_logger = setup_logging('conference-api', logging.DEBUG)
    _registry.replace("app_logger", app_logger)
    initialise_app_context()
    initialise_api_docs(app)

    # routes
    set_routes(app)
    list_routes(app)


# essential initialisation; accessible to Gunicorn and local execution by running server.py as `main`
initialise(app)

if __name__ == '__main__':
    app_logger.info("Starting conference API Server")
    app.run(host='0.0.0.0', port=5000)

