from flask import Flask
from dotenv import load_dotenv
# from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
import os
import logging


# scheduler = APScheduler()
app = Flask(__name__)
db_mysql = SQLAlchemy()
verbose = (os.getenv('DEBUG', 'False') == 'True')


def create_app():
    load_dotenv()
    logging.basicConfig(filename=os.getenv('LOG_FILE'), level=logging.INFO, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

    from .procs import procs
    app.register_blueprint(procs, url_prefix='/')

    return app