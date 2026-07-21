"""Chapter writing prompt templates.

This module defines the system and user prompt templates used by the
ChapterAgent to generate novel chapter content with consistent narrative
voice, pacing, and character portrayal.

Template variables:
    chapter_number: The sequential number of the chapter to write.
    title: The title of the chapter.
    previous_summary: Summary of preceding chapters for continuity.
    outline_context: Relevant outline sections for this chapter.
    characters: Character profiles appearing in this chapter.
    world_context: World setting details relevant to the chapter.
    requirements: Specific instructions or constraints for the chapter.
"""

CHAPTER_SYSTEM = """You are a novel writing assistant.

Write engaging chapter content following:
- Narrative Voice: Consistent point of view and tone
- Scene Construction: Vivid settings, authentic dialogue
- Pacing: Appropriate rhythm and tension
- Character Voice: Distinct voices for each character
- Show Don't Tell: Demonstrate emotions and themes through action

Guidelines:
1. Write in the established narrative voice
2. Include sensory details to create immersion
3. Balance exposition with action and dialogue
4. End chapters with appropriate hooks or transitions
5. Maintain consistency with previous chapters"""

CHAPTER_USER_TEMPLATE = """Write chapter {chapter_number} for a novel.

Title: {title}

Previous chapter summary:
{previous_summary}

Current outline context:
{outline_context}

Characters appearing in this chapter:
{characters}

World setting context:
{world_context}

Chapter requirements:
{requirements}

Write the chapter content in markdown."""
