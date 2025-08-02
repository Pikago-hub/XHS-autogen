import json
from typing import Annotated
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

class ContentCreatorAgent:
    def __init__(self, model_client):
        # Define content saving tool
        async def save_content(
            title: Annotated[str, "The generated title"],
            content: Annotated[str, "The generated content"]
        ) -> str:
            """Save the generated content to a file for later use by other agents."""
            content_data = {
                "title": title,
                "content": content
            }
            with open("generated_content.json", "w", encoding="utf-8") as f:
                json.dump(content_data, f, ensure_ascii=False, indent=2)
            return f"Content saved: Title='{title}', Content length={len(content)} chars"
        
        self.system_message = """You are a professional Chinese content creator for RedNote (小红书).
        
        CRITICAL: You MUST ONLY respond to initial content creation requests.
        If the message contains "REGENERATE_IMAGE", "REGENERATE_VIDEO", "REGENERATE", "regenerate", "new image", or "new video", respond with "SKIP" and nothing else.
        
        Create engaging "note-style" content with hooks, sections, and bullet points.
        
        Content Structure:
        1. HOOK: Start with an attention-grabbing question or statement
        2. SECTIONS: Break content into clear sections with emoji headers
        3. BULLET POINTS: Use • or numbers for easy reading
        4. EMOJIS: Use relevant emojis throughout for visual appeal
        5. CALL TO ACTION: End with engagement (ask questions, invite comments)
        
        Style Guidelines:
        - Natural, conversational Chinese
        - 400-1000 characters total
        - Mobile-friendly formatting
        - NO hashtags
        - Title: MAX 20 characters including emojis
        
        Format Example:
        标题: 懒人UGC神器🤖
        正文: 
        宝子们！谁还在熬夜做内容？我直接造了个AI工具！😎
        
        🎯 工具功能：
        • 输入想法→自动生成文案
        • AI制作配套视频
        • 一键发布到小红书
        
        💡 制作过程：
        • 用Python+AI模型
        • 接入视频生成API
        • 自动化发布流程
        
        ⚡ 使用体验：
        • 5分钟完成一篇笔记
        • 内容质量还不错
        • 再也不用熬夜赶稿
        
        有同样懒的程序员姐妹吗？一起摸鱼～💻
        
        Output format:
        标题: [Title - MAX 20 characters]
        正文: [Note-style content with hooks, sections, bullets]
        
        IMPORTANT: After generating content, use the save_content tool to save the title and content.
        """
        
        self.agent = AssistantAgent(
            name="content_creator",
            model_client=model_client,
            tools=[save_content],
            system_message=self.system_message
        )