from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.base import Handoff

class MediaSelectorAgent:
    def __init__(self):
        pass
        
    def custom_input_func(self, prompt: str) -> str:
        """Handle media selection between GPT-Image-1 and Seedance"""
        
        # Check for regeneration requests first  
        if "REGENERATE_" in prompt.upper() or any(keyword in prompt.lower() for keyword in ["user requested new", "regenerate"]):
            print("Detected regeneration request - processing automatically...")
            # For image regeneration
            if any(img_keyword in prompt.upper() for img_keyword in ["REGENERATE_IMAGE", "NEW IMAGE", "IMAGE"]):
                print("Auto-selecting GPT-Image-1 for image regeneration")
                return "User selected GPT-Image-1. Create image prompt."
            # For video regeneration  
            elif any(vid_keyword in prompt.upper() for vid_keyword in ["REGENERATE_VIDEO", "NEW VIDEO", "VIDEO"]):
                print("Auto-selecting Seedance for video regeneration")
                return "User selected Seedance. Create video prompt."
            else:
                print("Unknown regeneration type, skipping")
                return "SKIP"
        
        print(f"\n{'='*60}")
        print("MEDIA GENERATION SELECTION")
        print(f"{'='*60}")
        
        # Extract and display the generated content
        if "CONTENT_GENERATED:" in prompt:
            content_part = prompt.split("CONTENT_GENERATED:")[1].strip()
            print("\nGenerated Content:")
            print("-" * 40)
            print(content_part)
            print("-" * 40)
        
        print("\nChoose media generation method:")
        print("1. GPT-Image-1 - Generate image")
        print("2. Seedance - Generate video")
        print("3. Cancel workflow")
        
        while True:
            choice = input("\nYour choice (1/2/3 or press Enter for image): ").strip().lower()
            
            if choice == "" or choice == "1" or choice == "image" or choice == "dalle":
                # Generate image with GPT-Image-1
                return "User selected GPT-Image-1. Create image prompt."
            elif choice == "2" or choice == "video" or choice == "seedance":
                # Generate video with Seedance
                return "User selected Seedance. Create video prompt."
            elif choice == "3" or choice == "cancel":
                return "WORKFLOW_CANCELLED: User cancelled the workflow - WORKFLOW COMPLETE"
            else:
                print("Invalid choice. Please enter 1, 2, 3, or press Enter for default.")
    
    def create_agent(self):
        return UserProxyAgent(
            name="media_selector",
            description="Human agent for selecting between GPT-Image-1 image or Seedance video generation",
            input_func=self.custom_input_func
        )