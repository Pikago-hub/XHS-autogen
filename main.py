import asyncio
import os
from dotenv import load_dotenv
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.content_creator import ContentCreatorAgent
from agents.seedance_prompt_agent import SeedancePromptAgent
from agents.seedance_with_tools import SeedanceAPIAgent
from agents.gpt_image_prompt_agent import DallEPromptAgent
from agents.gpt_image_agent import GPT4oImageAgent
from agents.media_selector import MediaSelectorAgent
from agents.rednote_publisher import RedNotePublisherAgent
from agents.content_review_agent import ContentReviewAgent

load_dotenv()

async def main():
    # Initialize model client
    model_client = OpenAIChatCompletionClient(
        model="gpt-4.1",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create agents
    content_creator = ContentCreatorAgent(model_client).agent
    seedance_prompt_agent = SeedancePromptAgent(model_client).agent
    seedance_api = SeedanceAPIAgent(model_client)
    seedance_api_agent = seedance_api.agent
    gpt_image_prompt_agent = DallEPromptAgent(model_client).agent
    dalle_api = GPT4oImageAgent(model_client)
    gpt_image_api_agent = dalle_api.agent
    media_selector = MediaSelectorAgent()
    media_selector_agent = media_selector.create_agent()
    
    rednote_publisher = RedNotePublisherAgent(model_client)
    rednote_publisher_agent = rednote_publisher.agent
    content_review = ContentReviewAgent()
    content_review_agent = content_review.create_agent()
    
    # Create termination condition  
    termination = TextMentionTermination("WORKFLOW COMPLETE")
    
    # Create RoundRobinGroupChat that cycles back when regeneration is needed
    team = RoundRobinGroupChat(
        participants=[
            content_creator,           # 1. Creates content
            media_selector_agent,      # 2. User selects image or video  
            gpt_image_prompt_agent,    # 3a. If image: create prompt 
            gpt_image_api_agent,       # 4a. If image: generate image
            seedance_prompt_agent,     # 3b. If video: create prompt
            seedance_api_agent,        # 4b. If video: generate video
            content_review_agent,      # 5. Human review (post/edit/regenerate/cancel)
            rednote_publisher_agent    # 6. Publish to RedNote when approved
        ],
        termination_condition=termination
    )
    
    # Get user input for content idea
    content_idea = input("Enter your content idea: ")
    
    # Start the workflow with simple task
    task = f"Create RedNote content for: {content_idea}"
    
    # Run the team
    async for item in team.run_stream(task=task):
        # Check if it's a message or a result
        if hasattr(item, 'source') and hasattr(item, 'content'):
            print(f"\n[{item.source}]: {item.content}\n")
        elif hasattr(item, 'messages'):
            # This is a TaskResult
            print("\nWorkflow completed successfully!")
            print(f"Total messages: {len(item.messages)}")
    

if __name__ == "__main__":
    asyncio.run(main())