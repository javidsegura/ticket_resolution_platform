import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)


def escape_html(text: str) -> str:
	"""Escape HTML special characters in code blocks."""
	html_escape_map = {
		"&": "&amp;",
		"<": "&lt;",
		">": "&gt;",
		'"': "&quot;",
		"'": "&#039;",
	}
	return "".join(html_escape_map.get(char, char) for char in text)


def process_inline_markdown(text: str) -> str:
	"""Process inline markdown (bold, links, etc.)."""
	# Process bold
	text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)

	# Process links
	text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

	return text


def markdown_to_html(markdown: str) -> str:
	"""
	Convert markdown to HTML using the same logic as the TypeScript implementation.

	Args:
		markdown: Markdown string to convert

	Returns:
		HTML string representation of the markdown
	"""
	code_blocks: List[str] = []
	html = markdown

	# Step 1: Extract and replace code blocks first (to protect their content)
	def replace_code_block(match: re.Match) -> str:
		lang = match.group(1) if match.group(1) else None
		code = match.group(2)
		index = len(code_blocks)
		lang_attr = f' class="language-{lang}"' if lang else ""
		code_blocks.append(f"<pre><code{lang_attr}>{escape_html(code.strip())}</code></pre>")
		return f"\n__CODE_BLOCK_{index}__\n"

	html = re.sub(r"```(\w+)?\n?([\s\S]*?)```", replace_code_block, html)

	# Step 2: Extract and replace inline code
	inline_codes: List[str] = []

	def replace_inline_code(match: re.Match) -> str:
		code = match.group(1)
		index = len(inline_codes)
		inline_codes.append(f"<code>{escape_html(code)}</code>")
		return f"__INLINE_CODE_{index}__"

	html = re.sub(r"`([^`\n]+)`", replace_inline_code, html)

	# Step 3: Process line by line
	lines = html.split("\n")
	processed_lines: List[str] = []
	current_paragraph: List[str] = []
	in_list = False
	list_type: str | None = None
	list_items: List[str] = []

	def flush_paragraph():
		if current_paragraph:
			para_content = " ".join(current_paragraph).strip()
			if para_content and not re.match(r"^<(h[1-6]|ul|ol|pre|p|li)", para_content):
				processed_lines.append(f"<p>{para_content}</p>")
			elif para_content:
				processed_lines.append(para_content)
			current_paragraph.clear()

	def flush_list():
		nonlocal in_list, list_type
		if list_items and list_type:
			processed_lines.append(f"<{list_type}>{''.join(list_items)}</{list_type}>")
			list_items.clear()
			list_type = None
			in_list = False

	for line in lines:
		trimmed = line.strip()

		# Skip empty lines
		if not trimmed:
			flush_paragraph()
			flush_list()
			continue

		# Check for headers (must be at start of line)
		h3_match = re.match(r"^###\s+(.+)$", trimmed)
		if h3_match:
			flush_paragraph()
			flush_list()
			content = trimmed.replace("### ", "", 1)
			processed_lines.append(f"<h3>{process_inline_markdown(content)}</h3>")
			continue

		h2_match = re.match(r"^##\s+(.+)$", trimmed)
		if h2_match:
			flush_paragraph()
			flush_list()
			content = trimmed.replace("## ", "", 1)
			processed_lines.append(f"<h2>{process_inline_markdown(content)}</h2>")
			continue

		h1_match = re.match(r"^#\s+(.+)$", trimmed)
		if h1_match:
			flush_paragraph()
			flush_list()
			content = trimmed.replace("# ", "", 1)
			processed_lines.append(f"<h1>{process_inline_markdown(content)}</h1>")
			continue

		# Check for code blocks (placeholders)
		if re.match(r"^__CODE_BLOCK_\d+__$", trimmed):
			flush_paragraph()
			flush_list()
			processed_lines.append(trimmed)
			continue

		# Check for unordered list
		ul_match = re.match(r"^-\s+(.+)$", trimmed)
		if ul_match:
			flush_paragraph()
			content = trimmed.replace("- ", "", 1)
			if not in_list or list_type != "ul":
				flush_list()
				in_list = True
				list_type = "ul"
			list_items.append(f"<li>{process_inline_markdown(content)}</li>")
			continue

		# Check for ordered list
		ol_match = re.match(r"^\d+\.\s+(.+)$", trimmed)
		if ol_match:
			flush_paragraph()
			content = re.sub(r"^\d+\.\s+", "", trimmed)
			if not in_list or list_type != "ol":
				flush_list()
				in_list = True
				list_type = "ol"
			list_items.append(f"<li>{process_inline_markdown(content)}</li>")
			continue

		# Regular line - add to paragraph
		flush_list()
		current_paragraph.append(trimmed)

	# Flush remaining content
	flush_paragraph()
	flush_list()

	html = "\n".join(processed_lines)

	# Step 4: Restore inline code
	for index, code in enumerate(inline_codes):
		html = html.replace(f"__INLINE_CODE_{index}__", code)

	# Step 5: Restore code blocks
	for index, block in enumerate(code_blocks):
		html = html.replace(f"__CODE_BLOCK_{index}__", block)

	# Clean up extra whitespace
	html = re.sub(r"\n{3,}", "\n\n", html).strip()

	return html


async def get_markdown_from_container(container_path: str) -> str:
	"""
	Mock function to get markdown content from cloud storage (Azure Blob/S3).

	For now, this returns mock content. In production, this would fetch
	from actual storage using the storage service.

	Args:
		container_path: Path to the object in cloud storage (container/bucket agnostic)

	Returns:
		Markdown content as string
	"""
	# TODO: Replace with actual storage retrieval
	# storage = get_storage_service()
	# return storage.download_blob(container_path)

	# Mock implementation for now
	logger.info(f"Mocking markdown retrieval from container: {container_path}")

	# Extract intent_id from container_path if possible (e.g., "articles/article-123-...")
	intent_id_match = re.search(r"article-(\d+)", container_path)
	intent_id = intent_id_match.group(1) if intent_id_match else "unknown"

	mock_markdown = f"""# Article {intent_id}

This is a sample article for intent ID {intent_id}.

## Introduction

This content is loaded from a markdown file and converted to HTML for display.

## Features

- **Markdown support**: Full markdown syntax
- **HTML rendering**: Converted to HTML for display
- **Mock API**: Simulates the real API response

### Code Example

Here's some example code:

\`\`\`python
def hello_world():
	print("Hello, World!")
\`\`\`

## Conclusion

This is a test article to verify that the MicroAnswer component can display markdown content correctly.

You can use inline code like `print("test")` or links like [Example](https://example.com).
"""

	return mock_markdown


async def get_micro_answer_html(container_path: str) -> str:
	"""
	Get markdown from cloud storage and convert it to HTML.

	Args:
		container_path: Path to the markdown file in cloud storage (container/bucket agnostic)

	Returns:
		HTML content as string (body only, no full HTML document)
	"""
	try:
		markdown_content = await get_markdown_from_container(container_path)
		html_content = markdown_to_html(markdown_content)
		logger.debug(f"Successfully converted markdown to HTML for container: {container_path}")
		return html_content
	except Exception as e:
		logger.error(f"Error converting markdown to HTML for container {container_path}: {e}", exc_info=True)
		raise
