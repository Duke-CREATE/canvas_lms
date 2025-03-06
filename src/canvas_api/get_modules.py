import requests

def get_modules_and_video_links(base_url, access_token, course_id):
    """
    Fetching all modules and their video links from a specific course in Canvas LMS.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 1: Fetch all modules in the course
    modules_url = f"{base_url}/courses/{course_id}/modules"
    print(modules_url, headers)
    modules_response = requests.get(modules_url, headers=headers)
    if not modules_response.ok:
        print(modules_response.text)

    if modules_response.status_code != 200:
        print(f"Failed to fetch modules: {modules_response.status_code}")
        return {}

    modules = modules_response.json()
    modules_with_videos = {}

    # Step 2: Iterate through modules to get video links
    for module in modules:
        module_name = module.get("name", "Unnamed Module")
        module_id = module.get("id")
        
        if not module_id:
            continue

        # Fetch module items
        module_items_url = f"{base_url}/courses/{course_id}/modules/{module_id}/items"
        items_response = requests.get(module_items_url, headers=headers)

        if items_response.status_code != 200:
            print(f"Failed to fetch items for module {module_name}: {items_response.status_code}")
            continue

        module_items = items_response.json()
        video_links = []

        for item in module_items:
            if item.get("type") == "File":  # Check if the item is a file
                file_id = item.get("content_id")  # Get the file ID
                file_url = f"{base_url}/courses/{course_id}/files/{file_id}"
                video_links.append(file_url)

        if video_links:
            modules_with_videos[module_name] = video_links

    return modules_with_videos

