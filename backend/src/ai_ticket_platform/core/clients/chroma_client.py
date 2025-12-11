"""ChromaDB client wrapper for RAG document storage and retrieval."""

import asyncio
import logging
import threading
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

logger = logging.getLogger(__name__)


class ChromaVectorStore:
	"""ChromaDB wrapper for semantic document retrieval using LangChain."""

	def __init__(self, settings):
		"""
		Initialize ChromaDB client.

		Args:
		    settings: Application settings containing CHROMA_HOST, CHROMA_PORT, GEMINI_API_KEY
		"""
		self.chroma_host = settings.CHROMA_HOST
		self.chroma_port = settings.CHROMA_PORT
		self.collection_name = settings.CHROMA_COLLECTION_NAME or "company-docs"

		# Initialize ChromaDB HTTP client
		self.client = chromadb.HttpClient(
			host=self.chroma_host,
			port=self.chroma_port,
			settings=ChromaSettings(anonymized_telemetry=False),
		)

		# Initialize Gemini embeddings
		self.embeddings = GoogleGenerativeAIEmbeddings(
			google_api_key=settings.GEMINI_API_KEY,
			model="models/embedding-001",
		)

		# Text splitter for chunking documents
		self.text_splitter = RecursiveCharacterTextSplitter(
			chunk_size=1000,
			chunk_overlap=200,
			separators=["\n\n", "\n", ". ", " ", ""],
		)

		logger.info(
			f"Initialized ChromaDB client at {self.chroma_host}:{self.chroma_port}, collection: {self.collection_name}"
		)

	def get_or_create_collection(self):
		"""Get or create the ChromaDB collection."""
		try:
			collection = self.client.get_or_create_collection(
				name=self.collection_name,
				metadata={"description": "Company documentation for RAG"},
			)
			return collection
		except Exception as e:
			logger.error(f"Error getting/creating collection: {e}")
			raise

	async def index_document(
		self, file_id: int, filename: str, content: str, area: str
	) -> Dict:
		"""
		Chunk, embed, and index a single document to ChromaDB.

		Args:
		    file_id: Database ID of the file
		    filename: Original filename
		    content: Full document text content
		    area: Department area (e.g., "HR", "IT")

		Returns:
		    Dict with indexing status and counts
		"""
		try:
			# Chunk the document
			chunks = self.text_splitter.split_text(content)

			logger.info(f"Chunking {filename} into {len(chunks)} chunks")

			# Prepare documents and metadata for LangChain Chroma
			texts = []
			metadatas = []

			for chunk_index, chunk_text in enumerate(chunks):
				texts.append(chunk_text)
				metadatas.append(
					{
						"file_id": str(file_id),
						"filename": filename,
						"area": area,
						"chunk_index": chunk_index,
					}
				)

			# Remove existing chunks for this file before re-indexing to prevent stale chunks
			collection = self.get_or_create_collection()
			try:
				collection.delete(where={"file_id": str(file_id)})
				logger.info(f"Deleted existing chunks for file_id {file_id} before re-indexing")
			except Exception as e:
				logger.debug(f"No existing chunks to delete for file_id {file_id}: {e}")

			# Use LangChain Chroma to handle embedding and indexing
			vectorstore = Chroma(
				client=self.client,
				collection_name=self.collection_name,
				embedding_function=self.embeddings,
			)

			# Add documents with embeddings 
			ids = [f"{file_id}-{i}" for i in range(len(chunks))]
			await asyncio.to_thread(
				vectorstore.add_texts, texts=texts, metadatas=metadatas, ids=ids
			)

			logger.info(f"Successfully indexed {len(chunks)} chunks for {filename}")

			return {
				"status": "success",
				"total": len(chunks),
				"successful": len(chunks),
				"failed": 0,
			}

		except Exception as exc:
			logger.error(f"Error indexing document {file_id}: {exc}")
			return {
				"status": "error",
				"error": str(exc),
				"total": 0,
				"successful": 0,
				"failed": 0,
			}

	async def similarity_search(
		self, query: str, k: int = 5, area_filter: Optional[str] = None
	) -> List[Dict]:
		"""
		Perform similarity search on ChromaDB.

		Args:
		    query: Search query text
		    k: Number of results to return
		    area_filter: Optional filter by area (e.g., "HR", "IT")

		Returns:
		    List of dicts with content, filename, area, relevance_score
		"""
		logger.debug(
			f"Searching ChromaDB: query='{query[:50]}...', k={k}, area_filter={area_filter}"
		)

		try:
			# Initialize LangChain Chroma for retrieval
			vectorstore = Chroma(
				client=self.client,
				collection_name=self.collection_name,
				embedding_function=self.embeddings,
			)

			# Build filter for area if provided
			filter_dict = {"area": area_filter} if area_filter else None

			# Perform similarity search with scores (run in thread to avoid blocking event loop)
			results = await asyncio.to_thread(
				vectorstore.similarity_search_with_score,
				query=query, k=k, filter=filter_dict
			)

			# Format results
			retrieved_docs = []
			for doc, score in results:
				retrieved_docs.append(
					{
						"content": doc.page_content,
						"filename": doc.metadata.get("filename", "Unknown"),
						"area": doc.metadata.get("area", "Unknown"),
						"file_id": doc.metadata.get("file_id"),
						"chunk_index": doc.metadata.get("chunk_index", 0),
						"relevance_score": score,
					}
				)

			logger.info(f"Retrieved {len(retrieved_docs)} documents from ChromaDB")
			return retrieved_docs

		except Exception as e:
			logger.error(f"Error searching ChromaDB: {e}")
			raise

# Global vector store instance (initialized in lifespan)
chroma_vectorstore = None
_init_lock = threading.Lock()


def initialize_chroma_vectorstore(settings) -> ChromaVectorStore:
	"""
	Initialize the global ChromaDB vector store instance.

	Args:
	    settings: Application settings

	Returns:
	    ChromaVectorStore instance
	"""
	global chroma_vectorstore
	if not chroma_vectorstore:
		logger.info("Initializing ChromaDB vector store")
		chroma_vectorstore = ChromaVectorStore(settings)
	return chroma_vectorstore


def get_chroma_vectorstore(settings=None) -> ChromaVectorStore:
	"""
	Get or initialize the ChromaDB vector store.

	Args:
		settings: Optional application settings object. If None, will auto-initialize.

	Returns:
		ChromaVectorStore instance
	"""
	global chroma_vectorstore
	if chroma_vectorstore is None:
		with _init_lock:
			# Double-check inside lock to prevent race condition
			if chroma_vectorstore is None:
				if settings is None:
					# Auto-initialize settings if not provided
					from ai_ticket_platform.core.settings.app_settings import initialize_settings
					settings = initialize_settings()
				chroma_vectorstore = initialize_chroma_vectorstore(settings)
	return chroma_vectorstore
