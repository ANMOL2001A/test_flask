#!/bin/bash

# Upload the file and capture the response
upload_response=$(curl -F "file=@$1" http://localhost:5000/upload)

# Extract the upload ID from the response
upload_id=$(echo $upload_response | jq -r '.upload_id')

# Check if the upload ID is valid
if [ "$upload_id" == "null" ]; then
    echo "Failed to upload file."
    echo "Response: $upload_response"
    exit 1
fi

echo "File uploaded successfully. Tracking progress..."

# Loop to check the progress
while true; do
    progress_response=$(curl http://localhost:5000/upload/progress/$upload_id 2>/dev/null)
    progress=$(echo $progress_response | jq -r '.progress')
    if [[ $progress != "null" ]]; then
        echo "Upload progress: $progress%"
        if [[ $progress -eq 100 ]]; then
            echo "Upload complete."
            break
        fi
    else
        echo "Error: Invalid response. Exiting..."
        echo "Response: $progress_response"
        break
    fi
    sleep 1  # Adjust the interval as needed
done
