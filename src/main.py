import os
from canvas_api.get_modules import get_modules_and_video_links
from canvas_api.download_files import save_video_metadata
from dotenv import load_dotenv

load_dotenv()

# Canvas LMS configuration
BASE_URL = os.getenv("CANVAS_BASE_URL") 
ACCESS_TOKEN = os.getenv("CANVAS_ACCESS_TOKEN")

# Parameters
COURSE_ID = "11203383"  #course ID

def main():
    # Fetching modules and video links
    modules_with_videos = get_modules_and_video_links(BASE_URL, ACCESS_TOKEN, COURSE_ID)
    
    if modules_with_videos:
        print("Saving Video Metadata...")
        for module_name, video_links in modules_with_videos.items():
            print(f"\nModule: {module_name}")
            for link in video_links:
                # Preparing file data for saving in JSON
                file_metadata = {
                    "filename": link.split("/")[-1],
                    "url": link,
                }
                save_video_metadata(file_metadata)
        print("\nMetadata saved. Check the 'data' folder for video_metadata.json.")
    else:
        print("No video links found in the specified course.")

if __name__ == "__main__":
    main()


