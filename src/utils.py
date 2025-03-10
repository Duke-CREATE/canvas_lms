import os
import math
import glob
from moviepy import VideoFileClip
from pydub import AudioSegment
from openai import OpenAI
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError
from canvas_api.get_modules import get_modules_and_video_links
from canvas_api.download_files import save_video_metadata, get_file_download_url, download_video

def process_and_download_videos(base_url, access_token, course_id):
    """
    Processes modules to extract download URLs for videos, saves video metadata,
    and downloads each video as an .mp4 file.
    """
    modules_with_videos = get_modules_and_video_links(base_url, access_token, course_id)
    downloaded_paths = {}
    if modules_with_videos:
        print("Processing modules, extracting download URLs and downloading videos...")
        for module_name, video_links in modules_with_videos.items():
            print(f"\nModule: {module_name}")
            for link in video_links:
                # Get the actual download URL and display name from the API endpoint
                module_video_paths = []
                download_url, display_name = get_file_download_url(link, access_token)
                if download_url and display_name:
                    # Ensure the filename ends with .mp4
                    if not display_name.lower().endswith(".mp4"):
                        display_name += ".mp4"
                    
                    # Save video metadata for later use
                    file_metadata = {
                        "filename": display_name,
                        "url": download_url,
                    }
                    save_video_metadata(file_metadata)
                    
                    # Download the video using the extracted download URL
                    video_path = download_video(download_url, display_name, access_token)
                    if video_path:
                        module_video_paths.append(video_path)
                else:
                    print(f"Could not extract download URL from {link}")
            downloaded_paths[module_name] = module_video_paths
        print("\nMetadata saved. Videos downloaded.")
    else:
        print("No video links found in the specified course.")
    return downloaded_paths


def transcribe_mp4(video_path, chunk_duration_minutes=5):
    """
    Extracts audio from an .mp4 video, splits the audio into chunks,
    transcribes each chunk using the Whisper API, and returns the full transcription.

    :param video_path: Path to the input .mp4 video file.
    :param chunk_duration_minutes: Duration of each chunk in minutes (default 5).
    :return: A string containing the full transcription of the audio.
    """

    # -------------------------------------------------------------------
    # 1) EXTRACT AUDIO FROM VIDEO AND SAVE AS .MP3
    # -------------------------------------------------------------------
    audio_dir = os.path.join("..", "data", "audio")
    os.makedirs(audio_dir, exist_ok=True)
    try:
        # Load the video
        video = VideoFileClip(video_path)
        # Derive an MP3 filename from the MP4 path (same folder, same basename)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        audio_file = os.path.join(audio_dir, f"{base_name}.mp3")
        video.audio.write_audiofile(audio_file)
        print(f"Audio extracted and saved as {audio_file}")
    except Exception as e:
        print("Error extracting audio from video:", e)
        return ""

    # -------------------------------------------------------------------
    # 2) LOAD THE AUDIO AND SPLIT INTO CHUNKS
    # -------------------------------------------------------------------
    try:
        audio = AudioSegment.from_file(audio_file, format="mp3")
        print("Audio Imported ✅")

        # Calculate chunk sizes in milliseconds
        chunk_length_ms = chunk_duration_minutes * 60 * 1000
        total_length_ms = len(audio)
        num_chunks = math.ceil(total_length_ms / chunk_length_ms)

        # Create a folder to store chunks, e.g. "myvideo_chunks"
        chunk_folder = os.path.join(audio_dir, f"{base_name}_chunks")
        os.makedirs(chunk_folder, exist_ok=True)

        # Export each chunk as .mp3
        for i in range(num_chunks):
            start_ms = i * chunk_length_ms
            end_ms = min((i + 1) * chunk_length_ms, total_length_ms)
            chunk = audio[start_ms:end_ms]
            chunk_file = os.path.join(chunk_folder, f"{base_name}_{i}.mp3")
            chunk.export(chunk_file, format="mp3")

        print("Chunks created ✅")

    except Exception as e:
        print("Error creating audio chunks:", e)
        return ""

    # -------------------------------------------------------------------
    # 3) TRANSCRIBE AUDIO CHUNKS WITH OPENAI WHISPER
    # -------------------------------------------------------------------
    transcripts = []
    try:
        client = OpenAI()  # Based on your snippet - adjust if using 'import openai'
        # Find each chunk file in ascending order
        chunk_files = sorted(
            glob.glob(os.path.join(chunk_folder, f"{base_name}_*.mp3"))
        )

        for chunk_file in chunk_files:
            with open(chunk_file, "rb") as f:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", file=f
                )
                transcripts.append(transcription.text)

        full_transcription = " ".join(transcripts)
        print("Full transcription done ✅")

    except Exception as e:
        print("Error transcribing chunks:", e)
        return ""

    # -------------------------------------------------------------------
    # 4) RETURN THE COMBINED TRANSCRIPTION
    # -------------------------------------------------------------------
    return full_transcription


class TranscriptDB:
    """
    A class for interacting with the CanvasDB.Transcripts collection in MongoDB.
    """

    def __init__(self, connection_string: str):
        """
        Initializes the TranscriptDB instance with a MongoDB connection.

        Parameters:
            connection_string (str): The MongoDB connection string.
        """
        if not connection_string:
            raise ValueError("A valid connection string must be provided.")

        try:
            self.client = MongoClient(connection_string)
            self.db = self.client["CanvasDB"]
            self.collection = self.db["Transcripts"]
        except PyMongoError as e:
            raise ConnectionError("Failed to connect to MongoDB: " + str(e))

    def insert_transcript(
        self, transcript: str, file_name: str, course_name: str
    ) -> str:
        """
        Inserts a transcript document into the collection if the transcript is not empty.

        Parameters:
            transcript (str): The transcript text.
            file_name (str): The name of the file.
            course_name (str): The course name.

        Returns:
            str: The inserted document's id as a string if successful; an empty string otherwise.
        """
        if not transcript or not transcript.strip():
            print("Transcript is empty. Aborting upload.")
            return ""

        document = {
            "file_name": file_name,
            "transcript": transcript,
            "course_name": course_name,
        }

        try:
            result = self.collection.insert_one(document)
            print("Inserted document with id:", result.inserted_id)
            return str(result.inserted_id)
        except PyMongoError as e:
            print("Error inserting transcript:", e)
            return ""

    def get_transcript_by_id(self, doc_id: str) -> dict:
        """
        Retrieves a transcript document from the collection using its id.

        Parameters:
            doc_id (str): The id of the document to retrieve.

        Returns:
            dict: The document data if found; None otherwise.
        """
        try:
            obj_id = ObjectId(doc_id)
            document = self.collection.find_one({"_id": obj_id})
            if document is None:
                print("No document found with id:", doc_id)
            return document
        except Exception as e:
            print("Error retrieving transcript by id:", e)
            return None

    def close(self):
        """
        Closes the MongoDB connection.
        """
        self.client.close()
