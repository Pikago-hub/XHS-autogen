import os
import time
import asyncio
from typing import Annotated
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Handoff
from google import genai
from google.genai import types

class Veo3APIAgent:
    def __init__(self, model_client):
        # Configure Google AI
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_AI_API_KEY not found in environment variables")
            
        self.google_client = genai.Client(api_key=api_key)
        
        # Define the video generation tool
        async def generate_video(
            prompt: Annotated[str, "The detailed video prompt text"]
        ) -> str:
            """Generate a video using Google Veo3 API with the given prompt."""
            try:
                print(f"\nTOOL EXECUTION: Generating video with Veo3...")
                print(f"Prompt: {prompt[:100]}...")
                
                operation = self.google_client.models.generate_videos(
                    model="veo-3.0-fast-generate-preview",
                    prompt=prompt,
                    config=types.GenerateVideosConfig(
                        aspect_ratio="9:16"  # Portrait format for mobile video
                    )
                )
                
                # Poll until ready
                start_time = time.time()
                while not operation.done:
                    elapsed = int(time.time() - start_time)
                    print(f"Generating... ({elapsed}s elapsed)")
                    await asyncio.sleep(20)
                    operation = self.google_client.operations.get(operation)
                

                print(f"\nDEBUG: Full operation analysis:")
                print(f"   - operation.done: {operation.done}")
                print(f"   - operation type: {type(operation)}")
                
                if hasattr(operation, 'result'):
                    print(f"   - operation.result: {operation.result}")
                    if operation.result:
                        print(f"   - result type: {type(operation.result)}")
                        print(f"   - result dir: {[attr for attr in dir(operation.result) if not attr.startswith('_')]}")
                        if hasattr(operation.result, 'generated_videos'):
                            print(f"   - result.generated_videos: {operation.result.generated_videos}")
                

                if hasattr(operation, 'response'):
                    print(f"   - operation.response: {operation.response}")
                    if operation.response:
                        print(f"   - response type: {type(operation.response)}")
                        print(f"   - response dir: {[attr for attr in dir(operation.response) if not attr.startswith('_')]}")
                        if hasattr(operation.response, 'generated_videos'):
                            print(f"   - response.generated_videos: {operation.response.generated_videos}")
                            if operation.response.generated_videos:
                                print(f"   - videos count: {len(operation.response.generated_videos)}")
                

                videos = None
                if operation.response and hasattr(operation.response, 'generated_videos') and operation.response.generated_videos:
                    videos = operation.response.generated_videos
                    print("Found videos in operation.response.generated_videos")
                elif operation.result and hasattr(operation.result, 'generated_videos') and operation.result.generated_videos:
                    videos = operation.result.generated_videos
                    print("Found videos in operation.result.generated_videos")
                
                if videos and len(videos) > 0:
                    video = videos[0]
                    print(f"Video object: {video}")
                    print(f"Video type: {type(video)}")
                    print(f"Video attributes: {[attr for attr in dir(video) if not attr.startswith('_')]}")
                    
                    # Save with timestamp
                    timestamp = int(time.time())
                    filename = f"rednote_video_{timestamp}.mp4"
                    
                    print(f"\nDownloading video...")
                    try:
                        self.google_client.files.download(file=video.video)
                        video.video.save(filename)
                        
                        total_time = int(time.time() - start_time)
                        print(f"\nSuccess! Video saved as: {filename}")
                        
                        return f"""VIDEO_GENERATED: Successfully created video!

Filename: {filename}
Duration: 8 seconds
Audio: Included
Generation time: {total_time} seconds
Location: {os.path.abspath(filename)}

The video is ready for review."""
                    except Exception as download_error:
                        print(f"Error downloading video: {download_error}")
                        return f"Video generation completed but download failed: {download_error}"
                
                else:
                    print("No videos found in operation result or response")
                    print(f"Full operation object: {operation}")
                    return "Video generation failed - no video returned"
                    
            except Exception as e:
                return f"Error generating video: {str(e)}"
        
        self.agent = AssistantAgent(
            name="veo3_api_agent",
            model_client=model_client,
            tools=[generate_video],  
            system_message="""You are the Veo3 API agent responsible for generating videos.

CRITICAL: You MUST ONLY respond when you receive a detailed video prompt (long descriptive text about video elements, camera movement, etc.).
If the message contains "SKIP", "User selected GPT-Image-1", or mentions image generation, respond with "SKIP" and nothing else.
If no video prompt is present, respond with "SKIP" and nothing else.

When you receive an approved video prompt from veo3_prompt_engineer:
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