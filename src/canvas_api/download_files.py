import os
import json
import requests

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

def get_file_download_url(api_url, access_token):
    """
    Given an API URL for a file, fetch the file information and extract the
    actual download URL.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error accessing {api_url}: {e}")
        return None

    try:
        file_info = response.json()
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {api_url}: {e}")
        return None, None
    download_url = file_info.get("url")
    display_name = file_info.get("display_name")  # e.g. "xai_final_project.mp4"
    
    # Fallback: if display_name is missing, create a filename from the API URL
    if not display_name:
        display_name = api_url.split("/")[-1] + ".mp4"
    
    return download_url, display_name

def download_video(url, filename, access_token):
    """Download the video from the given URL and save it with the specified filename."""
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to download {filename}: {e}")
        return
    video_dir = "../data/videos"
    os.makedirs(video_dir, exist_ok=True)
    video_path = os.path.join(video_dir, filename)

    with open(video_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"Downloaded video: {video_path}")
    return video_path
