---
title: D&D 5e RAG Chat Assistant
emoji: 🎲
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---

# D&D 5e RAG Chat Assistant

A conversational AI assistant for searching Dungeons & Dragons 5e official books using RAG (Retrieval-Augmented Generation).

## Setup on Hugging Face Spaces

1. Add your secrets in Settings → Repository secrets:
   - `ANTHROPIC_API_KEY` - Your Anthropic API key (required)
   - `GITHUB_TOKEN` - Your GitHub token (optional)
   - `GITHUB_REPO` - Your GitHub repo in format `owner/repo` (optional)

2. Upload your PDF documents to the `data/` folder

3. The app will automatically initialize on first run

## Usage

Ask questions in natural language:
- "What are the character classes?"
- "Tell me about wizards"
- "How does combat work?"

The assistant will search documents and provide answers with source citations.
