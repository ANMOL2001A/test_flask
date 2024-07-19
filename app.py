from routes import api
from flasgger import Swagger
from flask_cors import CORS
from flask import Flask, jsonify, Response, render_template
#from logman import Logger
from datetime import datetime
from webserver import BeckHealthServer
import signal

app = BeckHealthServer(__name__)
app.config['DEBUG'] = True
CORS(app)

swagger = Swagger(app)

app.register_blueprint(api)

# logger_instance = Logger()
# logger = logger_instance.get_logger()


def handle_shutdown(signum, frame):
    shutdown_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #logger.info(f"Gunicorn is shutting down at {shutdown_time}")


signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


@app.route('/')
def home() -> Response:
    """
    Home route to test the server
    @param: None
    @return: Rendered HTML template
    """
    return render_template('index.html')


if __name__ == "__main__":
    app.run()
