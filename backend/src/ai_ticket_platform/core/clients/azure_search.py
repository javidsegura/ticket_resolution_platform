"""Azure AI Search client wrapper for RAG document retrieval."""

import logging
from typing import Dict, List, Optional, Tuple

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class _BaseAzureSearchClient:
	"""Shared Azure Search auth + client bootstrap."""

	def __init__(self, settings):
		self.endpoint = settings.AZURE_SEARCH_ENDPOINT
		self.index_name = settings.AZURE_SEARCH_INDEX_NAME or "company-docs"

		if hasattr(settings, "AZURE_SEARCH_KEY") and settings.AZURE_SEARCH_KEY:
			self.credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
			logger.info("Using Azure Search API Key for authentication")
		else:
			self.credential = DefaultAzureCredential()
			logger.info("Using DefaultAzureCredential for Azure Search")

		self.search_client = SearchClient(
			endpoint=self.endpoint,
			index_name=self.index_name,
			credential=self.credential,
		)

		self.embeddings = GoogleGenerativeAIEmbeddings(
			google_api_key=settings.GEMINI_API_KEY,
			model="models/embedding-001",
		)


class AzureSearchVectorStore(_BaseAzureSearchClient):
	"""Azure AI Search wrapper for semantic document retrieval."""

	def __init__(self, settings):
		"""Initialize Azure AI Search retrieval client."""
		super().__init__(settings)
		logger.info(f"Initialized Azure Search client for index '{self.index_name}'")

	async def similarity_search(
		self, query: str, k: int = 5, area_filter: Optional[str] = None
	) -> List[Tuple[Dict, float]]:
		"""
		Perform hybrid search (semantic + keyword) on Azure AI Search.
		"""
		logger.debug(
			f"Searching Azure AI Search: query='{query[:50]}...', k={k}, area_filter={area_filter}"
		)

		try:
			# Generate query embedding using Gemini
			query_vector = await self.embeddings.aembed_query(query)

			# Build filter string for area if provided
			filter_expr = f"area eq '{area_filter}'" if area_filter else None

			# Perform hybrid search (vector + text)
			results = self.search_client.search(
				search_text=query,  # Keyword search
				vector_queries=[
					VectorizedQuery(
						vector=query_vector,
						k_nearest_neighbors=k,
						fields="content_vector",
					)
				],
				filter=filter_expr,
				top=k,
				select=[
					"id",
					"content",
					"filename",
					"area",
					"chunk_index",
					"file_id",
				],
			)

			# Convert results to (metadata, score) tuples
			retrieved_docs = []
			for result in results:
				metadata = {
					"id": result.get("id"),
					"content": result.get("content"),
					"filename": result.get("filename", "Unknown"),
					"area": result.get("area", "Unknown"),
					"chunk_index": result.get("chunk_index", 0),
					"file_id": result.get("file_id"),
				}
				score = result.get("@search.score", 0.0)
				retrieved_docs.append((metadata, score))

			logger.info(
				f"Retrieved {len(retrieved_docs)} documents from Azure AI Search"
			)
			return retrieved_docs

		except Exception as e:
			logger.error(f"Error searching Azure AI Search: {e}")
			raise


class AzureSearchIndexer(_BaseAzureSearchClient):
	"""Azure AI Search indexer that chunks, embeds, and uploads documents."""
	def __init__(self, settings):
		super().__init__(settings)
		self.index_client = SearchIndexClient(
			endpoint=self.endpoint,
			credential=self.credential,
		)
		self.text_splitter = RecursiveCharacterTextSplitter(
			chunk_size=1000,
			chunk_overlap=200,
			separators=["\n\n", "\n", ". ", " ", ""],
		)

	async def index_document(
		self, file_id: int, filename: str, content: str, area: str
	) -> Dict:
		"""Chunk, embed, and upload a single document."""
		try:
			chunks = self.text_splitter.split_text(content)
			documents = []
			for chunk_index, chunk_text in enumerate(chunks):
				chunk_embedding = await self.embeddings.aembed_query(chunk_text)
				documents.append(
					{
						"id": f"{file_id}-{chunk_index}",
						"file_id": str(file_id),
						"filename": filename,
						"area": area,
						"chunk_index": chunk_index,
						"content": chunk_text,
						"content_vector": chunk_embedding,
					}
				)

			result = self.search_client.upload_documents(documents=documents)
			successful = sum(1 for r in result if r.succeeded)
			failed = len(result) - successful

			return {
				"status": "success",
				"total": len(result),
				"successful": successful,
				"failed": failed,
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


# Global vector store instance (initialized in lifespan)
azure_search_store = None
azure_search_indexer = None


def initialize_azure_search(settings) -> AzureSearchVectorStore:
	"""
	Initialize the global Azure Search vector store instance.

	Args:
	    settings: Application settings

	Returns:
	    AzureSearchVectorStore instance
	"""
	global azure_search_store
	if not azure_search_store:
		logger.info("Initializing Azure AI Search vector store")
		azure_search_store = AzureSearchVectorStore(settings)
	return azure_search_store


def get_azure_search() -> AzureSearchVectorStore:
	"""Get the initialized Azure Search vector store instance."""
	if not azure_search_store:
		raise RuntimeError(
			"Azure Search not initialized. Call initialize_azure_search first."
		)
	return azure_search_store


def initialize_azure_search_indexer(settings) -> AzureSearchIndexer:
	"""Initialize the global Azure Search indexer."""
	global azure_search_indexer
	if not azure_search_indexer:
		logger.info("Initializing Azure AI Search indexer")
		azure_search_indexer = AzureSearchIndexer(settings)
	return azure_search_indexer


def get_azure_search_indexer() -> AzureSearchIndexer:
	if not azure_search_indexer:
		raise RuntimeError(
			"Azure Search indexer not initialized. Call initialize_azure_search_indexer first."
		)
	return azure_search_indexer
