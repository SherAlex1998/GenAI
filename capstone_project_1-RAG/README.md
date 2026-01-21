# D&D 5e RAG Chat Assistant

A conversational AI assistant for searching Dungeons & Dragons 5e official books using RAG (Retrieval-Augmented Generation).

![Screenshot](screenshot/example.png)

## Features

- **Document Search**: Find information in D&D 5e PDF books with source citations
- **AI Chat**: Natural language interface powered by Claude
- **Support Tickets**: Create GitHub Issues directly from chat
- **Multilingual**: English interface, Russian document support

## Tech Stack

- **LLM**: Anthropic Claude (Haiku 4.5)
- **Embeddings**: Sentence Transformers (multilingual MiniLM)
- **Vector Store**: FAISS
- **Framework**: LangChain
- **UI**: Streamlit

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```env
ANTHROPIC_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here  # optional
GITHUB_REPO=owner/repo         # optional
```

3. Add PDF documents to `data/` folder

4. Run the app:
```bash
streamlit run app.py
```

## Project Structure

```
├── app.py              # Streamlit UI
├── chat_agent.py       # Agent logic with tools
├── rag_processor.py    # Document processing & search
├── github_tool.py      # GitHub Issues integration
└── data/               # PDF documents folder
```

## Usage

Ask questions in natural language:
- "What are the character classes?"
- "Tell me about wizards"
- "How does combat work?"

The assistant will search documents and provide answers with source citations.

## Docker Deployment

### Build and run locally:

```bash
docker build -t dnd-rag-chat .
docker run -p 7860:7860 --env-file .env -v $(pwd)/data:/app/data dnd-rag-chat
```

### Deploy to Hugging Face Spaces:

1. Create a new Space on Hugging Face
2. Choose "Docker" as SDK
3. Upload files: `Dockerfile`, `*.py`, `requirements.txt`
4. Rename `README_HF.md` to `README.md` in the Space
5. Add secrets: `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `GITHUB_REPO`
6. Upload PDFs to `data/` folder
