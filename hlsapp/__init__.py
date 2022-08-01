from flask import Flask
from dotenv import load_dotenv
import os
import logging


# scheduler = APScheduler()
app = Flask(__name__)

def create_app():
    load_dotenv()
    logging.basicConfig(filename=os.getenv('LOG_FILE'), level=logging.INFO, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

    from .procs import procs
    app.register_blueprint(procs, url_prefix='/')

    return app