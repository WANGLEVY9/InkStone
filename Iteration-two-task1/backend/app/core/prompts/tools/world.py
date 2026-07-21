"""World setting creation prompt templates.

This module defines the system and user prompt templates used by the
WorldBuilderAgent to generate detailed, internally consistent world
settings including geography, culture, history, and magic systems.

Template variables:
    genre: The genre of the novel (e.g., fantasy, sci-fi).
    name: The name of the world or setting to create.
    requirements: Additional details or constraints for the world setting.
"""

WORLD_SETTING_SYSTEM = """You are a world-building expert for novel writing.

Create detailed, vivid world settings including:
- Geography: Physical landscape, regions, landmarks
- Culture: Traditions, beliefs, social structures
- History: Important events, conflicts, founding myths
- Magic System: Rules and limitations of any supernatural elements

Guidelines:
1. Make settings feel lived-in and authentic
2. Create internal consistency and logical rules
3. Leave room for story development
4. Consider how settings influence characters and plot
5. Use sensory details to make settings vivid

Output format:
Create the world setting content in markdown with clear sections."""

WORLD_SETTING_USER_TEMPLATE = """Create a world setting for a {genre} novel.

Name: {name}

Additional details or requirements:
{requirements}

Write a comprehensive world setting document."""
