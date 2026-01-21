FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including git-lfs
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Initialize git-lfs
RUN git lfs install

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY chat_agent.py .
COPY rag_processor.py .
COPY github_tool.py .

# Copy data files (LFS files will be pulled automatically)
COPY data/ ./data/

# Create vector store directory (will be populated on first run if empty)
RUN mkdir -p vector_store

# Expose Streamlit port
EXPOSE 7860

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=7860
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
