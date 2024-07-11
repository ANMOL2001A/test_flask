from flask import Flask, jsonify, request
import os
import hashlib
import json
import logging
from werkzeug.utils import secure_filename
from helper import UploadInput

app = Flask(__name__)

UPLOAD_FOLDER = 'dataset'
HASH_FILE = 'hash.json'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(HASH_FILE):
    with open(HASH_FILE, 'w') as hash_file:
        json.dump({}, hash_file)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

error_messages = {
    "400": "Bad request, no file part in the request",
    "500": "Internal server error",
    "501": "File already exists",
    "502": "No dataset directory to reset",
    "503": "Failed to reset dataset"
}

@app.route('/')
def home():
    return "Welcome to the File Upload API! Use the /upload endpoint to upload your files."

@app.route('/upload', methods=['POST'])
def upload_file():
    logging.info('Received a request to upload a file.')

    if 'file' not in request.files:
        error_message = error_messages["400"]
        logging.error(f"Error uploading file: {error_message}")
        return jsonify({"error": error_message}), 400

    file_data = request.files['file']
    if file_data.filename == '':
        error_message = error_messages["400"]
        logging.error(f"Error uploading file: {error_message}")
        return jsonify({"error": error_message}), 400

    filename = secure_filename(file_data.filename)

    # Validate the file extension
    try:
        UploadInput.validate_file_extension(filename)
    except ValueError as e:
        error_message = str(e)
        logging.error(f"Error uploading file: {error_message}")
        return jsonify({"error": error_message}), 400

    file_path = os.path.join(UPLOAD_FOLDER, filename)

    file_data.seek(0)
    file_hash = calculate_file_hash(file_data.stream)

    try:
        with open(HASH_FILE, 'r') as hash_file:
            hash_data = json.load(hash_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading hash data: {str(e)}")
        hash_data = {}

    if file_hash in hash_data.values():
        error_message = error_messages["501"]
        logging.error(f"Duplicate file detected: {error_message}")
        return jsonify({"error": error_message}), 400

    try:
        file_data.seek(0)
        file_data.save(file_path)
        logging.info(f"File saved successfully at: {file_path}")
    except Exception as e:
        error_message = error_messages["500"]
        logging.error(f"Error saving file: {str(e)}")
        return jsonify({"error": error_message, "details": str(e)}), 500

    try:
        hash_data[filename] = file_hash
        with open(HASH_FILE, 'w') as hash_file:
            json.dump(hash_data, hash_file)
        logging.info(f"Hash data updated successfully for file: {filename}")
    except Exception as e:
        error_message = error_messages["500"]
        logging.error(f"Error updating hash data: {str(e)}")
        return jsonify({"error": error_message, "details": str(e)}), 500

    return jsonify({"message": "File uploaded successfully", "file_path": file_path}), 200


def calculate_file_hash(file_stream):
    hasher = hashlib.sha256()
    file_stream.seek(0)
    chunk_size = 4096
    while True:
        chunk = file_stream.read(chunk_size)
        if not chunk:
            break
        hasher.update(chunk)
    file_stream.seek(0)
    return hasher.hexdigest()


if __name__ == "__main__":
    app.run(debug=True)
