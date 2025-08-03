import os
import time
import asyncio
import requests
from typing import Annotated
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Handoff

class SeedanceAPIAgent:
    def __init__(self, model_client):
        api_key = os.getenv("ARK_API_KEY")
        if not api_key:
            raise ValueError("ARK_API_KEY not found in environment variables")
            
        self.api_key = api_key
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
        
        # Define the video generation tool
        async def generate_video(
            prompt: Annotated[str, "The detailed video prompt text"]
        ) -> str:
            """Generate a video using Seedance 1.0 Pro API with the given prompt."""
            try:
                print(f"\nTOOL EXECUTION: Generating video with Seedance 1.0 Pro...")
                print(f"Prompt: {prompt[:100]}...")
                
                # Add ratio to prompt for 9:16 portrait 
                formatted_prompt = f"{prompt} --ratio 9:16"
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                payload = {
                    "model": "doubao-seedance-1-0-pro-250528",
                    "content": [
                        {
                            "type": "text",
                            "text": formatted_prompt
                        }
                    ]
                }
                
                # Make the API request
                response = requests.post(self.api_url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    return f"Error: API request failed with status {response.status_code}: {response.text}"
                
                result = response.json()
                
                # Check if request was accepted
                if "id" not in result:
                    return f"Error: Unexpected API response format: {result}"
                
                task_id = result["id"]
                print(f"Generation started with task ID: {task_id}")
                
                # Poll for completion
                start_time = time.time()
                poll_url = f"https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{task_id}"
                
                while True:
                    elapsed = int(time.time() - start_time)
                    
                    # Check status
                    poll_headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                    status_response = requests.get(poll_url, headers=poll_headers)
                    if status_response.status_code != 200:
                        return f"Error: Status check failed: {status_response.text}"
                    
                    status_data = status_response.json()
                    
                    if status_data.get("status") == "succeeded":
                        # Get the video URL from res
                        content = status_data.get("content", {})
                        video_url = content.get("video_url")
                        
                        if not video_url:
                            return f"Error: No video URL found in response. Full response: {status_data}"
                        
                        # Extract video metadata
                        resolution = status_data.get("resolution", "1080p")
                        duration = status_data.get("duration", 5)
                        ratio = status_data.get("ratio", "9:16")
                        
                        print(f"\nDownloading video from: {video_url}")
                        video_response = requests.get(video_url)
                        
                        if video_response.status_code != 200:
                            return f"Error: Failed to download video: {video_response.status_code}"
                        
                        # Save the video
                        timestamp = int(time.time())
                        filename = f"rednote_video_{timestamp}.mp4"
                        
                        with open(filename, "wb") as f:
                            f.write(video_response.content)
                        
                        total_time = int(time.time() - start_time)
                        print(f"\nSuccess! Video saved as: {filename}")
                        
                        return f"""VIDEO_GENERATED: Successfully created video!

Filename: {filename}
Resolution: {resolution} ({ratio})
Duration: {duration} seconds
Generation time: {total_time} seconds
Location: {os.path.abspath(filename)}

The video is ready for review."""
                    
                    elif status_data.get("status") == "failed":
                        return f"Error: Video generation failed: {status_data.get('error', 'Unknown error')}"
                    
                    # Continue polling
                    print(f"Generating... ({elapsed}s elapsed) Status: {status_data.get('status', 'unknown')}")
                    await asyncio.sleep(5)
                    
                    # Timeout after 10 minutes
                    if elapsed > 600:
                        return "Error: Video generation timed out after 10 minutes"
                    
            except Exception as e:
                return f"Error generating video: {str(e)}"
        
        self.agent = AssistantAgent(
            name="seedance_api_agent",
            model_client=model_client,
            tools=[generate_video],  
            system_message="""You are the Seedance API agent responsible for generating videos.

CRITICAL: You MUST ONLY respond when you receive a detailed video prompt (long descriptive text about video elements, camera movement, etc.).
If the message contains "SKIP", "User selected GPT-Image-1", or mentions image generation, respond with "SKIP" and nothing else.
If no video prompt is present, respond with "SKIP" and nothing else.

When you receive an approved video prompt from seedance_prompt_engineer:
1. Extract the prompt text (remove any approval messages or quotes)
2. Call the generate_video tool with the clean prompt text
3. Return the result

IMPORTANT: You MUST use the generate_video tool. Do not describe what you would do - actually call the tool.""",
            handoffs=[
                Handoff(
                    target="rednote_publisher",
                    name="post_to_rednote", 
                    message="Video generated. Ready to post to RedNote."
                )
            ]
        )