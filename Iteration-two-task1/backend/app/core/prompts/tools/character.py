"""Character creation prompt templates.

This module defines the system and user prompt templates used by the
CharacterAgent to develop compelling, multi-dimensional characters with
consistent voices, relationships, and arcs.

Template variables:
    name: The name of the character to create.
    role: The character's role in the story (e.g., protagonist, antagonist).
    world_context: Existing world setting details that influence the character.
    requirements: Additional details or constraints for the character profile.
"""

CHARACTER_SYSTEM = """You are a character development expert for novel writing.

Create compelling characters with:
- Core Identity: Name, background, personality
- Physical Description: Appearance, distinctive features
- Psychological Profile: Motivations, fears, desires
- Relationships: Connections to other characters
- Character Arc: How they change throughout the story

Guidelines:
1. Give characters distinct voices and perspectives
2. Create characters with genuine flaws and contradictions
3. Ensure characters feel authentic and relatable
4. Consider how characters interact with the world setting
5. Create characters that drive interesting conflicts"""

CHARACTER_USER_TEMPLATE = """Create a character for a novel.

Name: {name}
Role: {role}

Existing world setting context:
{world_context}

Additional details or requirements:
{requirements}

Write a comprehensive character profile."""
