"""Simplified LangGraph RAG workflow for article generation - retrieve and generate only."""

import logging
from typing import Annotated, Dict, List, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from ai_ticket_platform.core.clients.azure_search import AzureSearchVectorStore

logger = logging.getLogger(__name__)


class RAGState(TypedDict):
	"""Simplified state for RAG workflow - retrieve and generate only."""

	# Input fields
	intent_id: int
	intent_name: str
	category: str
	subcategory: str
	ticket_summaries: List[str]
	area: str

	# Iteration fields (for regeneration with feedback)
	is_iteration: bool  # True if regenerating
	previous_article_content: Optional[str]  # Previous version
	previous_article_title: Optional[str]
	human_feedback: Optional[str]  # Feedback from human reviewer
	iteration_number: int  # 1 = first gen, 2 = first iterate, etc.

	# Processing fields
	messages: Annotated[List, add_messages]
	retrieved_docs: List[Dict]
	context: str

	# Output fields
	article_title: str
	article_content: str
	article_summary: str


class RAGWorkflow:
	"""Simplified LangGraph RAG workflow - retrieve and generate only."""

	def __init__(self, vector_store: AzureSearchVectorStore, settings):
		"""
		Initialize RAG workflow.
		"""
		self.vector_store = vector_store
		self.settings = settings

		# Initialize Gemini LLM
		self.llm = ChatGoogleGenerativeAI(
			google_api_key=settings.GEMINI_API_KEY,
			model=settings.GEMINI_MODEL or "gemini-1.5-pro",
			temperature=0.3,
		)

		# Build workflow graph
		self.workflow = self._build_workflow()

	def _build_workflow(self) -> StateGraph:
		"""
		Build the LangGraph workflow.

		Steps:
		1. retrieve: Retrieve relevant documents from Azure AI Search
		2. generate_article: Generate/regenerate article (with feedback if iteration)
		"""
		workflow = StateGraph(RAGState)

		# Add nodes
		workflow.add_node("retrieve", self._retrieve_documents)
		workflow.add_node("generate_article", self._generate_article)

		# Define edges (linear flow: retrieve -> generate -> end)
		workflow.set_entry_point("retrieve")
		workflow.add_edge("retrieve", "generate_article")
		workflow.add_edge("generate_article", END)

		return workflow.compile()

	async def _retrieve_documents(self, state: RAGState) -> RAGState:
		"""Retrieve relevant documents from Azure AI Search."""
		logger.info(f"Retrieving documents for intent: {state['intent_name']}")

		# Build query from intent name + ticket summaries
		query = self._build_retrieval_query(
			state["intent_name"],
			state["ticket_summaries"],
		)

		# Retrieve from Azure AI Search
		results = await self.vector_store.similarity_search(
			query=query,
			k=5,
			area_filter=state.get("area"),
		)

		# Format retrieved documents
		retrieved_docs = [
			{
				"content": metadata.get("content", ""),
				"filename": metadata.get("filename", "Unknown"),
				"area": metadata.get("area", "Unknown"),
				"relevance_score": score,
			}
			for metadata, score in results
		]

		logger.info(f"Retrieved {len(retrieved_docs)} documents from Azure AI Search")

		# Build context from retrieved docs
		context = self._build_context(retrieved_docs) if retrieved_docs else ""

		return {
			**state,
			"retrieved_docs": retrieved_docs,
			"context": context,
		}

	async def _generate_article(self, state: RAGState) -> RAGState:
		"""Generate or regenerate article (with feedback if iteration)."""
		is_iteration = state.get("is_iteration", False)

		if is_iteration:
			logger.info(
				f"ITERATING article (iteration #{state['iteration_number']}) with feedback"
			)
			return await self._regenerate_with_feedback(state)
		else:
			logger.info("Generating INITIAL article")
			return await self._generate_initial_article(state)

	async def _generate_initial_article(self, state: RAGState) -> RAGState:
		"""Generate initial article (first time)."""
		system_prompt = """You are an expert technical writer creating support articles for a help center.
							Your task:
							1. Analyze user tickets (common issues/questions)
							2. Use company documentation as your knowledge base
							3. Create a comprehensive, well-structured support article

							Requirements:
							- Clear, actionable title
							- Step-by-step instructions where applicable
							- Simple language (avoid jargon)
							- Include warnings/notes from company docs
							- Be empathetic to user frustrations

							Output format:
							TITLE: [Article title]
							SUMMARY: [1-2 sentence summary]
							CONTENT: [Full article in markdown]
							"""

		user_prompt = f"""Create a support article for:
						**Category**: {state['category']} > {state['subcategory']}
						**Intent**: {state['intent_name']}

						**User Issues** (from {len(state['ticket_summaries'])} tickets):
						{chr(10).join(f"{i+1}. {s}" for i, s in enumerate(state['ticket_summaries'][:10]))}

						**Company Documentation**:
						{state['context']}

						Generate a comprehensive article addressing these issues using the company docs.
"""

		messages = [
			SystemMessage(content=system_prompt),
			HumanMessage(content=user_prompt),
		]

		response = await self.llm.ainvoke(messages)
		article_text = response.content

		# Parse article
		title, summary, content = self._parse_article(article_text)

		logger.info(f"Generated initial article: {title}")

		return {
			**state,
			"article_title": title,
			"article_summary": summary,
			"article_content": content,
		}

	async def _regenerate_with_feedback(self, state: RAGState) -> RAGState:
		"""Regenerate article incorporating human feedback."""
		system_prompt = """You are an expert technical writer IMPROVING a support article based on human feedback.
						Your task:
						1. Read the previous article version
						2. Understand the human feedback
						3. Generate an IMPROVED version addressing the feedback
						4. Maintain accuracy to company documentation
						5. Keep the same overall structure unless feedback says otherwise

						Requirements:
						- Address ALL points in the feedback
						- Maintain or improve clarity
						- Use company docs as source of truth
						- Keep it concise and actionable
						"""

		user_prompt = f"""IMPROVE this article based on feedback:
						**Previous Article**:
						Title: {state['previous_article_title']}
						Content:
						{state['previous_article_content']}

						**Human Feedback** (iteration #{state['iteration_number']}):
						{state['human_feedback']}

						**Context** (same as before):
						Category: {state['category']} > {state['subcategory']}
						Intent: {state['intent_name']}

						User Issues:
						{chr(10).join(f"- {s}" for s in state['ticket_summaries'][:5])}

						**Company Documentation** (for reference):
						{state['context'][:3000]}... (use if needed for improvements)

						Generate an IMPROVED article that:
						1. Addresses the human feedback
						2. Maintains accuracy
						3. Improves on the previous version

						Output format:
						TITLE: [Improved title]
						SUMMARY: [Improved summary]
						CONTENT: [Improved content in markdown]
						"""

		messages = [
			SystemMessage(content=system_prompt),
			HumanMessage(content=user_prompt),
		]

		response = await self.llm.ainvoke(messages)
		article_text = response.content

		# Parse article
		title, summary, content = self._parse_article(article_text)

		logger.info(f"Regenerated article with feedback: {title}")

		return {
			**state,
			"article_title": title,
			"article_summary": summary,
			"article_content": content,
		}

	def _build_retrieval_query(
		self, intent_name: str, ticket_summaries: List[str]
	) -> str:
		"""Build query for document retrieval."""
		query_parts = [intent_name]
		query_parts.extend(ticket_summaries[:3])
		return " ".join(query_parts)

	def _build_context(self, retrieved_docs: List[Dict]) -> str:
		"""Build formatted context from retrieved documents."""
		context_parts = []
		for i, doc in enumerate(retrieved_docs, 1):
			context_parts.append(
				f"[Document {i}: {doc['filename']} - {doc['area']}]\n{doc['content']}\n"
			)
		return "\n---\n".join(context_parts)

	def _parse_article(self, article_text: str) -> tuple[str, str, str]:
		"""Parse article from LLM response."""
		lines = article_text.split("\n")

		title = "Untitled Article"
		summary = ""
		content = article_text

		for i, line in enumerate(lines):
			if line.startswith("TITLE:"):
				title = line.replace("TITLE:", "").strip()
			elif line.startswith("SUMMARY:"):
				summary = line.replace("SUMMARY:", "").strip()
			elif line.startswith("CONTENT:"):
				content = "\n".join(lines[i + 1 :]).strip()
				break

		return title, summary, content

	async def run(self, input_state: Dict) -> Dict:
		"""
		Run the RAG workflow (retrieve and generate only).
		"""
		logger.info(f"Starting RAG workflow for intent: {input_state['intent_name']}")

		try:
			# Initialize state
			initial_state: RAGState = {
				"intent_id": input_state["intent_id"],
				"intent_name": input_state["intent_name"],
				"category": input_state.get("category", "General"),
				"subcategory": input_state.get("subcategory", "Other"),
				"ticket_summaries": input_state["ticket_summaries"],
				"area": input_state.get("area", ""),
				# Iteration fields
				"is_iteration": input_state.get("is_iteration", False),
				"previous_article_content": input_state.get(
					"previous_article_content"
				),
				"previous_article_title": input_state.get("previous_article_title"),
				"human_feedback": input_state.get("human_feedback"),
				"iteration_number": input_state.get("iteration_number", 1),
				# Processing
				"messages": [],
				"retrieved_docs": [],
				"context": "",
				"article_title": "",
				"article_content": "",
				"article_summary": "",
			}

			# Run workflow
			final_state = await self.workflow.ainvoke(initial_state)

			logger.info("RAG workflow completed successfully")

			return {
				"status": "success",
				"article_title": final_state["article_title"],
				"article_summary": final_state["article_summary"],
				"article_content": final_state["article_content"],
				"retrieved_docs_count": len(final_state["retrieved_docs"]),
				"is_iteration": final_state["is_iteration"],
				"iteration_number": final_state["iteration_number"],
			}

		except Exception as e:
			logger.error(f"RAG workflow failed: {e}")
			return {
				"status": "error",
				"error": str(e),
			}
