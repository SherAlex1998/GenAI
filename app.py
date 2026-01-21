import streamlit as st
from pathlib import Path
from chat_agent import RAGChatAgent

if Path(".env").exists():
    from dotenv import load_dotenv
    load_dotenv()


def init_session():
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False


def init_rag():
    if not st.session_state.initialized:
        with st.spinner('Initializing RAG system...'):
            try:
                st.session_state.agent = RAGChatAgent()
                st.session_state.agent.initialize_rag()
                st.session_state.initialized = True
                st.success('RAG system ready!')
            except Exception as e:
                st.error(f'Error: {str(e)}')
                return False
    return True


st.set_page_config(page_title="D&D 5e RAG Chat", page_icon="🎲", layout="wide")

st.title("🎲 D&D 5e RAG Chat Assistant")
st.markdown("""
Welcome to the D&D 5e chat assistant!

**Features:**
- 📚 Search information in official D&D 5e books (Russian language)
- 💬 Get answers with source citations and page numbers
- 🎫 Create support requests (GitHub Issues)
""")

init_session()

with st.sidebar:
    st.header("⚙️ Settings")

    st.subheader("📄 Available Documents")
    data_path = Path("data")
    if data_path.exists():
        pdf_files = list(data_path.glob("*.pdf"))
        if pdf_files:
            for pdf in pdf_files:
                st.text(f"• {pdf.name}")
        else:
            st.warning("No PDF files found")
    else:
        st.error("data/ folder not found")

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        if st.session_state.agent:
            st.session_state.agent.clear_history()
        st.rerun()

    st.markdown("---")
    st.subheader("ℹ️ Help")
    st.markdown("""
    **Example Questions:**
    - What are the character classes?
    - Tell me about wizards
    - How does combat work?

    **Creating GitHub Issue:**
    - I want to report an issue
    - Create a support ticket
    """)

if not st.session_state.initialized:
    if not init_rag():
        st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about D&D 5e..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.agent.chat(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error = f"Error: {str(e)}"
                st.error(error)
                st.session_state.messages.append({"role": "assistant", "content": error})
