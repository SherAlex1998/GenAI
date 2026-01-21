import os
from pathlib import Path
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage

from rag_processor import RAGProcessor
from github_tool import create_github_issue

# Load .env only if file exists (for local development)
if Path(".env").exists():
    from dotenv import load_dotenv
    load_dotenv()


class RAGChatAgent:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Please set it in environment variables or .env file")

        self.llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            anthropic_api_key=self.api_key,
            temperature=0.7,
            max_tokens=4096
        )

        self.rag = RAGProcessor()
        self.chat_history = []
        self.agent = self._create_agent()

    def _create_agent(self):
        rag = self.rag

        @tool
        def search_documents(query: str) -> str:
            """Search for information in D&D 5e PDF documents"""
            try:
                results = rag.search(query, k=3)
                if not results:
                    return "No information found"

                response = "Found information:\n\n"
                for i, doc in enumerate(results, 1):
                    source = doc.metadata.get('source', 'Unknown')
                    page = doc.metadata.get('page', 'Unknown')
                    content = doc.page_content[:500]
                    response += f"[{i}] Source: {source}, Page: {page + 1}\n{content}...\n\n"

                return response
            except Exception as e:
                return f"Search error: {str(e)}"

        @tool
        def create_issue(username: str, email: str, title: str, description: str) -> str:
            """Create a GitHub Issue for support requests"""
            return create_github_issue(username, email, title, description)

        system_prompt = """You are a helpful assistant for D&D 5e documents and support.

Rules:
1. Always cite source (file name) and page number when providing information
2. If user wants to create GitHub Issue, ask for: name, email, title, description
3. Answer in Russian if asked in Russian, otherwise answer in English
4. Use search_documents tool to find information in PDF documents"""

        return create_agent(self.llm, tools=[search_documents, create_issue], system_prompt=system_prompt)

    def chat(self, user_input: str) -> str:
        try:
            messages = self.chat_history + [HumanMessage(content=user_input)]
            response = self.agent.invoke({"messages": messages})

            if response and "messages" in response:
                last_message = response["messages"][-1]
                answer = last_message.content if hasattr(last_message, 'content') else str(last_message)

                self.chat_history.append(HumanMessage(content=user_input))
                self.chat_history.append(AIMessage(content=answer))

                return answer

            return "Could not get response"
        except Exception as e:
            return f"Error: {str(e)}"

    def clear_history(self):
        self.chat_history = []

    def initialize_rag(self, force_rebuild: bool = False):
        print("Initializing RAG system...")
        self.rag.create_vector_store(force_rebuild=force_rebuild)
        print("RAG system ready!")
