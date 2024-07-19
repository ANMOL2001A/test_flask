from flask import Blueprint, jsonify, request, current_app as app
import os
import hashlib
import json
import logging
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
import math

api = Blueprint('handle', __name__, url_prefix='/api')

UPLOAD_FOLDER = 'dataset'
HASH_FILE = 'hash.json'
TEMP_FOLDER = 'temp'


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
if not os.path.exists(HASH_FILE):
    with open(HASH_FILE, 'w') as hash_file:
        json.dump({}, hash_file)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

upload_progress = {}

error_messages = {
    "400": "Bad request, no file part in the request",
    "500": "Internal server error",
    "501": "File already exists",
    "502": "No dataset directory to reset",
    "503": "Failed to reset dataset"
}

@api.route('/block_size', methods=['GET'])
def get_block_size():
    block_size = os.statvfs('/').f_bsize
    return jsonify({"block_size": block_size}), 200

@api.route('/total_chunks', methods=['POST'])
def get_total_chunks():
    data = request.get_json()
    if 'file_size' not in data or 'block_size' not in data:
        return jsonify({"error": "Missing file size or block size"}), 400

    file_size = data['file_size']
    block_size = data['block_size']
    total_chunks = math.ceil(file_size / block_size)
    
    return jsonify({"total_chunks": total_chunks}), 200

@api.route('/upload_chunk', methods=['POST'])
def upload_file_chunk():
    if 'file' not in request.files or 'chunk' not in request.form or 'total_chunks' not in request.form or 'filename' not in request.form:
        app.logger.error("Missing file or chunk metadata")
        return jsonify({"error": "Missing file or chunk metadata"}), 400

    file_data = request.files['file']
    chunk = int(request.form['chunk'])
    total_chunks = int(request.form['total_chunks'])
    filename = secure_filename(request.form['filename'])

    if file_data.filename == '':
        app.logger.error("No selected file")
        return jsonify({"error": "No selected file"}), 400

    temp_file_path = os.path.join(TEMP_FOLDER, filename)# default temp folder of os
    with open(temp_file_path, 'ab') as f:
        f.write(file_data.read())

    if chunk == total_chunks - 1:
        full_file_hash = calculate_file_hash(temp_file_path)

        with open(HASH_FILE, 'r') as hash_file:
            hash_data = json.load(hash_file)

        if full_file_hash in hash_data.values():
            os.remove(temp_file_path)
            error_message = error_messages["501"]
            app.logger.error(f"Duplicate file detected: {error_message}")
            return jsonify({"error": error_message}), 400

        final_file_path = os.path.join(UPLOAD_FOLDER, filename)
        os.rename(temp_file_path, final_file_path)

        hash_data[filename] = full_file_hash
        with open(HASH_FILE, 'w') as hash_file:
            json.dump(hash_data, hash_file)

    progress = int((chunk + 1) / total_chunks * 100)
    app.logger.info(f"Chunk {chunk + 1}/{total_chunks} uploaded. Progress: {progress}%")
    return jsonify({"message": "Chunk uploaded successfully", "progress": progress}), 200


def calculate_file_hash(file_path):
    hasher = hashlib.sha256()
    chunk_size = 4096
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def get_hash_file_path():
    return HASH_FILE
