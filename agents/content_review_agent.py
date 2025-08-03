import os
import re
from autogen_agentchat.agents import UserProxyAgent

class ContentReviewAgent:
    def __init__(self):
        pass
        
    def custom_input_func(self, prompt: str) -> str:
        """Handle content review and posting decisions"""
        
        print(f"DEBUG - Content reviewer triggered...")
        print(f"DEBUG - Received prompt (first 500 chars): {prompt[:500]}...")
        
        # Look for recently generated media files in the current directory
        import glob
        import time
        
        # Find recent image and video files 
        current_time = time.time()
        recent_files = []
        
        # Check for image files
        for image_file in glob.glob("gpt_image_*.png"):
            file_time = os.path.getmtime(image_file)
            if current_time - file_time < 300:  
                recent_files.append(image_file)
        
        # Check for video files (rednote/seedance patterns)
        video_patterns = ["rednote_video_*.mp4"]
        for pattern in video_patterns:
            for video_file in glob.glob(pattern):
                file_time = os.path.getmtime(video_file)
                if current_time - file_time < 300:  
                    recent_files.append(video_file)
        
        if recent_files:
            # Use the most recent media file
            recent_files.sort(key=os.path.getmtime, reverse=True)
            media_path = recent_files[0]
            print(f"DEBUG - Found recent media file: {media_path}")
            
            # Read the saved content from file
            title = ""
            content = ""
            
            try:
                import json
                with open("generated_content.json", "r", encoding="utf-8") as f:
                    content_data = json.load(f)
                    title = content_data.get("title", "")
                    content = content_data.get("content", "")
                    print(f"DEBUG - Loaded from file: title='{title[:30]}...', content length={len(content)}")
            except Exception as e:
                print(f"DEBUG - Could not load content from file: {e}")
                title = "Generated Content (Edit if needed)"
                content = "Please update this content as needed"
            
            return self.handle_review_interaction(title, content, media_path)
        
        # If no recent media files found, skip
        print("DEBUG - No recent media files found, skipping")
        return "SKIP"
    
    def handle_review_interaction(self, title, content, media_path):
        """Handle the actual user interaction for review"""
        
        # Display review information
        print("\n" + "="*60)
        print("FINAL REVIEW BEFORE POSTING TO REDNOTE")
        print("="*60)
        print(f"Title: {title}")
        
        # Check title length (max 20 characters)
        title_length = len(title)
        if title_length > 20:
            print(f"WARNING: Title is {title_length} characters (limit: 20)")
            print("   This may cause posting to fail!")
        else:
            print(f"Title length: {title_length}/20 characters")
        
        print(f"Content: {content}")
        print(f"Media: {media_path}")
        
        # Check if media file exists and determine type
        if os.path.exists(media_path):
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            media_type = "video" if file_ext in ['.mp4', '.mov', '.avi', '.mkv'] else "image"
            print(f"{media_type.title()} file size: {file_size/1024/1024:.1f} MB")
            print(f"File type: {file_ext}")
        else:
            print("Media file not found!")
            return f"ERROR: Media file not found: {media_path}"
        
        print("\n" + "-"*40)
        print("Options:")
        print("1. post - Post to RedNote")
        print("2. edit - Modify content before posting") 
        print("3. regenerate - Generate a new image/video")
        print("4. cancel - Cancel posting")
        print("-"*40)
        
        choice = input("\nYour decision (1/2/3/4 or press Enter to post): ").lower().strip()
        
        if choice == "" or choice in ["1", "post"]:
            return f"POST_APPROVED: {title}|{content}|{media_path}"
        elif choice in ["2", "edit"]:
            new_title = input(f"\nNew title (current: {title}): ").strip()
            new_content = input(f"\nNew content (current: {content[:50]}...): ").strip()
            
            if new_title:
                title = new_title
            if new_content:
                content = new_content
            

            return f"EDIT_CONTENT: Title: {title}, Content: {content}, Media: {media_path}"
        elif choice in ["3", "regenerate"]:
            print("\nRegenerating media...")
            file_ext = os.path.splitext(media_path)[1].lower()
            media_type = "video" if file_ext in ['.mp4', '.mov', '.avi', '.mkv'] else "image"
            return f"REGENERATE_{media_type.upper()}: Title: {title}, Content: {content}"
        else:
            return "CANCEL_POSTING: User cancelled the workflow"
    
    def create_agent(self):
        return UserProxyAgent(
            name="content_reviewer",
            description="Human agent for reviewing content before posting to RedNote",
            input_func=self.custom_input_func
        )