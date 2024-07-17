from flask import Blueprint, jsonify, request, current_app as app
import os
import hashlib
import json
import logging
from werkzeug.utils import secure_filename
from helper import UploadInput 
from flask_socketio import SocketIO, emit
import math


api = Blueprint('handle', __name__, url_prefix='/api')

UPLOAD_FOLDER = 'dataset'
HASH_FILE = 'hash.json'

# Ensure upload folder and hash file exist
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

api = Blueprint('handle', __name__, url_prefix='/api')

@api.route('/block_size', methods=['GET'])
def get_block_size():
    block_size = os.statvfs('/').f_bsize
    return jsonify({"block_size": block_size}), 200

@api.route('/total_chunks', methods=['POST'])
def get_total_chunks():
    data = request.get_json()
    if 'file_size' not in data:
        return jsonify({"error": "Missing file size"}), 400

    file_size = data['file_size']
    block_size = os.statvfs('/').f_bsize
    total_chunks = math.ceil(file_size / block_size)
    
    return jsonify({"total_chunks": total_chunks}), 200


@api.route('/upload_chunk', methods=['POST'])
def upload_file_chunk():
    """
    Upload a file in chunks.
    ---
    tags:
      - upload
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: The file chunk to upload.
      - in: formData
        name: chunk
        type: integer
        required: true
        description: The chunk number being uploaded.
      - in: formData
        name: total_chunks
        type: integer
        required: true
        description: The total number of chunks.
    responses:
      200:
        description: Chunk uploaded successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: A success message.
                progress:
                  type: integer
                  description: The current upload progress as a percentage.
      400:
        description: Bad request, no file part in the request
      500:
        description: Internal server error
    """
    if 'file' not in request.files or 'chunk' not in request.form or 'total_chunks' not in request.form:
        app.logger.error("Missing file or chunk metadata")
        return jsonify({"error": "Missing file or chunk metadata"}), 400

    file_data = request.files['file']
    chunk = int(request.form['chunk'])
    total_chunks = int(request.form['total_chunks'])

    if file_data.filename == '':
        app.logger.error("No selected file")
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file_data.filename)
    dataset_dir = UPLOAD_FOLDER
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)

    file_path = os.path.join(dataset_dir, filename)

    try:
        with open(file_path, 'ab') as f:
            f.seek(chunk * os.statvfs('/').f_bsize)
            f.write(file_data.read())

        progress = int((chunk + 1) / total_chunks * 100)
        app.logger.info(f"Chunk {chunk + 1}/{total_chunks} uploaded. Progress: {progress}%")
        return jsonify({"message": "Chunk uploaded successfully", "progress": progress}), 200
    except Exception as e:
        app.logger.error(f"Error uploading chunk: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

def calculate_file_hash(file_stream):
    hasher = hashlib.sha256()
    chunk_size = 4096
    while True:
        chunk = file_stream.read(chunk_size)
        if not chunk:
            break
        hasher.update(chunk)
    file_stream.seek(0)
    return hasher.hexdigest()

def get_hash_file_path():
    return HASH_FILE