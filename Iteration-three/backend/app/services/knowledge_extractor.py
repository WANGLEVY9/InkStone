"""Knowledge extraction from AI-generated text using LLM calls.

Extracts structured knowledge (facts, events, relationships, foreshadowing)
from natural language content produced during chat conversations.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypedDict

from app.services.llm import create_llm_client

logger = logging.getLogger("knowledge_extractor")

EXTRACTION_SYSTEM_PROMPT = """You are a novel knowledge extractor. Extract structured knowledge from the given novel writing text.

Output ONLY a valid JSON object with these keys (use empty arrays if nothing found):

1. "time_events": Array of objects with {title, description, chapter_number (int or null), involved_entities (string or null), event_type ("plot"|"character_change"|"world_change")}
2. "facts": Array of objects with {entity_type ("character"|"world_setting"|"plot_event"|"custom"), entity_id (string), fact_key (string), fact_value (string), summary (string)}
3. "relationships": Array of objects with {source_entity_id (string), target_entity_id (string), relationship_type (string), description (string or null)}
4. "foreshadowing": Array of objects with {description (string), related_chapter_id (string or null)}

Rules:
- entity_id should be the character or entity name in Chinese (e.g., "李逍遥", "蜀山")
- fact_key uses snake_case English (e.g., "cultivation_level", "background", "personality", "death_status", "identity")
- fact_value stores the actual value as a JSON string
- summary is a Chinese sentence describing the fact
- Only extract information that is explicitly stated or strongly implied in the text
- Do NOT invent or hallucinate information

Example:
Input: "李逍遥现在已经是金丹期修士了，他拜酒剑仙为师。"
Output: {"time_events": [], "facts": [{"entity_type": "character", "entity_id": "李逍遥", "fact_key": "cultivation_level", "fact_value": "金丹期", "summary": "李逍遥修为达到金丹期"}, {"entity_type": "character", "entity_id": "李逍遥", "fact_key": "master", "fact_value": "酒剑仙", "summary": "李逍遥拜酒剑仙为师"}], "relationships": [{"source_entity_id": "李逍遥", "target_entity_id": "酒剑仙", "relationship_type": "master", "description": "酒剑仙是李逍遥的师父"}], "foreshadowing": []}
"""


class ExtractionResult(TypedDict):
    time_events: list[dict[str, Any]]
    facts: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    foreshadowing: list[dict[str, Any]]


class KnowledgeExtractor:
    """Uses an LLM to extract structured knowledge from text content."""

    def __init__(self, llm: Any | None = None) -> None:
        self.llm = llm or create_llm_client(streaming=False)

    async def extract(self, text: str) -> ExtractionResult:
        """Extract structured knowledge from text content.

        Args:
            text: The text content to extract knowledge from.

        Returns:
            ExtractionResult with time_events, facts, relationships, foreshadowing.

        Raises:
            ValueError: If LLM response cannot be parsed as valid JSON.
        """
        try:
            result = await self.llm.ainvoke(
                [
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Extract knowledge from this text:\n\n{text}"},
                ]
            )
            content = result.content if hasattr(result, "content") else str(result)
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                content = "".join(text_parts)

            content_str = str(content).strip()
            # Handle potential markdown code blocks
            if "```json" in content_str:
                content_str = content_str.split("```json")[1].split("```")[0].strip()
            elif "```" in content_str:
                content_str = content_str.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content_str)
            return ExtractionResult(
                time_events=parsed.get("time_events", []),
                facts=parsed.get("facts", []),
                relationships=parsed.get("relationships", []),
                foreshadowing=parsed.get("foreshadowing", []),
            )
        except (json.JSONDecodeError, Exception) as exc:
            logger.warning("Knowledge extraction failed: %s", exc)
            return ExtractionResult(time_events=[], facts=[], relationships=[], foreshadowing=[])
