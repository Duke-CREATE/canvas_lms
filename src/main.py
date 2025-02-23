import os
from canvas_api.get_modules import get_modules_and_video_links
from canvas_api.download_files import save_video_metadata, download_video, get_file_download_url
from dotenv import load_dotenv
from utils import *

load_dotenv()

# Canvas LMS configuration
BASE_URL = os.getenv("CANVAS_BASE_URL") 
ACCESS_TOKEN = os.getenv("CANVAS_ACCESS_TOKEN")

# Parameters
COURSE_ID = "11203383"  #course ID

def main():
    video_path = process_and_download_videos(BASE_URL, ACCESS_TOKEN, COURSE_ID)
    for module, paths in video_path.items():
        print(f"\nProcessing module: {module}")
        for video_path in paths:
            # Transcribe the video
            transcription_text = transcribe_mp4(video_path)
            print("\nFINAL TRANSCRIPTION:\n", transcription_text[:100])
            
            # Get the connection string from the environment variables
            conn_str = os.getenv("connection_string")
            if not conn_str:
                raise ValueError("connection_string not found in environment variables.")
            
            # Create an instance of TranscriptDB and insert the transcript
            db_instance = TranscriptDB(conn_str)
            # Using module as an example course label here; you can adjust as needed.
            doc_id = db_instance.insert_transcript(transcription_text, video_path, module)
            
            # Retrieve and print the inserted transcript document if insertion was successful.
            if doc_id:
                document = db_instance.get_transcript_by_id(doc_id)
                print("Retrieved document:", document)
            
            # Close the database connection after each operation.
            db_instance.close()

if __name__ == "__main__":
    main()


