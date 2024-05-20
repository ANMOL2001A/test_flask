from flask import Flask, jsonify, request
import os
import hashlib
from werkzeug.utils import secure_filename

app = Flask(__name__)


@app.route('/')
def home():
    return "Welcome to the File Upload API! Use the /upload endpoint to upload your files."


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload a file.
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
        description: The file to upload (must be a Markdown (.md) file).
    responses:
      200:
        description: File uploaded successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: A success message.
                file_path:
                  type: string
                  description: The path where the file is saved.
      400:
        description: Bad request, no file part in the request
      500:
        description: Internal server error
    """

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file_data = request.files['file']
    filename = secure_filename(file_data.filename)

    dataset_dir = "dataset"  # Assuming dataset directory exists
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)

    file_path = os.path.join(dataset_dir, filename)

    file_hash = calculate_file_hash(file_data.stream)

    try:
        file_data.save(file_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not os.path.exists(file_path):
        return jsonify({"error": "Failed to save the file"}), 500

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
