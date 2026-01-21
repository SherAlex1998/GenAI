from typing import List
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


class HuggingFaceEmbeddings(Embeddings):
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([text], convert_to_numpy=True)[0].tolist()


class RAGProcessor:
    def __init__(self, data_folder: str = "data", vector_store_path: str = "vector_store"):
        self.data_folder = data_folder
        self.vector_store_path = vector_store_path
        self.embeddings = HuggingFaceEmbeddings()
        self.vector_store = None

    def _load_pdfs(self) -> List[Document]:
        documents = []
        for pdf_file in Path(self.data_folder).glob("*.pdf"):
            print(f"Loading: {pdf_file.name}")
            docs = PyPDFLoader(str(pdf_file)).load()
            for doc in docs:
                doc.metadata['source'] = pdf_file.name
            documents.extend(docs)

        print(f"Loaded {len(documents)} pages")
        return documents

    def _split_documents(self, documents: List[Document]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks")
        return chunks

    def create_vector_store(self, force_rebuild: bool = False):
        store_path = Path(self.vector_store_path)
        index_file = store_path / "index.faiss"

        if index_file.exists() and not force_rebuild:
            print("Loading existing vector store...")
            try:
                self.vector_store = FAISS.load_local(
                    self.vector_store_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Failed to load vector store: {e}")
                print("Creating new vector store...")
                force_rebuild = True

        if not index_file.exists() or force_rebuild:
            print("Creating vector store from PDFs...")
            documents = self._load_pdfs()
            chunks = self._split_documents(documents)
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)

            # Create directory if it doesn't exist
            store_path.mkdir(parents=True, exist_ok=True)
            self.vector_store.save_local(self.vector_store_path)
            print("Vector store created and saved")

        print("Vector store ready")
        return self.vector_store

    def search(self, query: str, k: int = 4) -> List[Document]:
        if self.vector_store is None:
            self.create_vector_store()
        return self.vector_store.similarity_search(query, k=k)
