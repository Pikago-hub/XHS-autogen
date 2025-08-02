# Quick Start Guide

## 1. Set up environment

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install playwright browsers
playwright install chromium
```

## 2. Configure API keys

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# For now, you only need:
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

## 3. Run the workflow

```bash
python main.py
```

## What will happen:

1. You'll be prompted to enter a content idea
2. The AI will generate Chinese content for RedNote
3. You'll review and approve the content
4. The AI will create a Veo3 video prompt
5. You'll review the video prompt
6. The workflow completes

## Example interaction:

```
Enter your content idea: A cozy coffee shop in Tokyo during cherry blossom season

=== AI generates Chinese content ===
标题: 东京樱花季的温馨咖啡店☕️🌸
正文: 在东京的小巷里，发现了这家超有氛围的咖啡店...
标签: #东京咖啡店 #樱花季 #日本旅行

=== You review ===
Options:
1. approve - Approve and continue
2. reject - Reject and stop
3. edit - Request modifications

Your choice: approve

=== AI creates Veo3 prompt ===
{
  "prompt": "Cozy Japanese coffee shop interior with cherry blossoms visible through windows...",
  "style": "cinematic",
  "duration": "15",
  ...
}
```