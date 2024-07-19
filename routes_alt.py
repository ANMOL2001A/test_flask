from flask import Blueprint, jsonify, request, current_app as app, Response
import os
import hashlib
import json
import logging
import math
from werkzeug.utils import secure_filename
import time

api = Blueprint('handle', __name__, url_prefix='/api')

UPLOAD_FOLDER = 'dataset'
HASH_FILE = 'hash.json'
TEMP_FOLDER = 'temp_uploads'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

if not os.path.exists(HASH_FILE):
    with open(HASH_FILE, 'w') as hash_file:
        json.dump({}, hash_file)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_block_size():
    return os.statvfs('/').f_bsize

@api.route('/block_size', methods=['GET'])
def get_block_size_route():
    return jsonify({"block_size": get_block_size()}), 200

@api.route('/total_chunks', methods=['POST'])
def get_total_chunks():
    data = request.json
    if not data or 'file_size' not in data or 'block_size' not in data:
        return jsonify({"error": "Missing file_size or block_size"}), 400
    
    file_size = data['file_size']
    block_size = data['block_size']
    total_chunks = math.ceil(file_size / block_size)
    
    return jsonify({"total_chunks": total_chunks}), 200

@api.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'block_size' not in request.form or 'total_chunks' not in request.form:
        return jsonify({"error": "Missing file, block_size, or total_chunks"}), 400

    file = request.files['file']
    block_size = int(request.form['block_size'])
    total_chunks = int(request.form['total_chunks'])

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    temp_file_path = os.path.join(TEMP_FOLDER, filename)

    try:
        file.save(temp_file_path)
        return Response(process_file(temp_file_path, filename, block_size, total_chunks),
                        content_type='text/event-stream')
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({"error": str(e)}), 500


def process_file(temp_file_path, filename, block_size, total_chunks):
    try:
        file_hash = calculate_file_hash(temp_file_path, block_size)

        with open(HASH_FILE, 'r') as hash_file:
            hash_data = json.load(hash_file)

        if file_hash in hash_data.values():
            os.remove(temp_file_path)
            return f"data: {json.dumps({'error': 'File already exists'})}\n\n"
            
        final_file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(temp_file_path, 'rb') as src:
            with open(final_file_path, 'wb') as dst:
                for chunk in range(total_chunks):
                    data = src.read(block_size)
                    dst.write(data)
                    progress = (chunk + 1) * 100 // total_chunks
                    logger.info(f"Chunk {chunk + 1}/{total_chunks} processed. Progress: {progress}%")
                    yield f"data: {json.dumps({'progress': progress})}\n\n"
                    
        os.remove(temp_file_path)

        hash_data[filename] = file_hash
        with open(HASH_FILE, 'w') as hash_file:
            json.dump(hash_data, hash_file)

        yield f"data: {json.dumps({'message': 'File uploaded and processed successfully', 'progress': 100})}\n\n"

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


def calculate_file_hash(file_path, block_size):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(block_size)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()