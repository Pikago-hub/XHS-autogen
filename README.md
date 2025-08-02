# RedNote Auto-Publisher

An intelligent multi-agent system that creates, generates media for, and publishes content to RedNote (小红书) automatically.

## Overview

This project uses Microsoft's AutoGen framework to orchestrate multiple AI agents that work together to:

1. Generate engaging Chinese content based on your ideas
2. Create accompanying images or videos
3. Review and edit content before posting
4. Automatically publish to RedNote

## Workflow

### Agent Pipeline

```
User Input → Content Creator → Media Selector → Media Generator → Content Review → RedNote Publisher
```

### Detailed Workflow

1. **Content Creation**

   - Input: Your content idea (can be in Chinese or English)
   - Agent: `ContentCreatorAgent`
   - Output: Chinese title (max 20 chars) and engaging content formatted for RedNote

2. **Media Selection**

   - Choice between:
     - GPT-Image-1: Fast image generation (default, press Enter)
     - Veo3: Video generation (takes longer, ~2-3 minutes)
   - Agent: `MediaSelectorAgent`

3. **Media Generation**

   - **For Images**:
     - `DallEPromptAgent` creates detailed image prompts in structured JSON format
     - `GPT4oImageAgent` generates images using OpenAI's GPT-Image-1 model
   - **For Videos**:
     - `Veo3PromptAgent` creates cinematic video prompts
     - `Veo3APIAgent` generates 8-second videos using Google's Veo3 API

4. **Content Review**

   - Agent: `ContentReviewAgent`
   - Options:
     - **Post** (default, press Enter): Approve and post to RedNote
     - **Edit**: Modify title/content before posting
     - **Regenerate**: Create new image/video with same content
     - **Cancel**: Stop the workflow

5. **Publishing**
   - Agent: `RedNotePublisherAgent`
   - Features:
     - Automatic QR code login (first time only)
     - Session persistence for future posts
     - Headless browser automation
     - Screenshot verification

### Regeneration Flow

When you select "regenerate" during review:

- The workflow intelligently skips content creation and media selection
- Goes directly to generating new media with the same content
- Returns to review with the new media

## Quick Start

### 1. Set up environment

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install playwright browsers
playwright install chromium
```

### 2. Configure API keys

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your keys:
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_AI_API_KEY=your-google-ai-key-here  # Optional, for Veo3 video generation
```

### 3. Run the workflow

```bash
python main.py
```

### 4. Follow the interactive prompts

1. Enter your content idea
2. Select media type (or press Enter for image)
3. Review the generated content and media
4. Choose to post, edit, regenerate, or cancel
5. For first-time posting, scan the QR code in the browser window
