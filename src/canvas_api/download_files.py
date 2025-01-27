import os
import json

def save_video_metadata(file_data, save_dir="../data"):
    """
    Save the video file metadata (filename and URL) to a JSON file in the data directory.

    """
    file_url = file_data.get("url")
    file_name = file_data.get("filename")

    if not file_url or not file_name:
        print("Invalid file data. URL or filename is missing.")
        return

    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Path for the JSON file
    json_file_path = os.path.join(save_dir, "video_metadata.json")

    # Load existing metadata if the file exists
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as json_file:
            metadata = json.load(json_file)
    else:
        metadata = {}

    # Add the new video metadata
    metadata[file_name] = file_url

    # Save the updated metadata to the JSON file
    with open(json_file_path, "w") as json_file:
        json.dump(metadata, json_file, indent=4)

    print(f"Metadata saved for file: {file_name}")
