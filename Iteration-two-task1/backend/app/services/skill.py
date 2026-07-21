"""SkillService for managing skill files stored as markdown with YAML frontmatter.

Skills are stored in ``backend/data/skills/{name}.md`` with YAML frontmatter
containing metadata (name, description, domain, tags) and a markdown body
containing the full prompt content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class SkillService:
    """Manage skill files as markdown with YAML frontmatter.

    Attributes:
        skills_dir: Directory where skill markdown files are stored.
    """

    def __init__(self, skills_dir: Path | None = None) -> None:
        """Initialize the service with an optional skills directory.

        Args:
            skills_dir: Path to the skills directory. Defaults to
                ``backend/data/skills/`` relative to the project root.
        """
        self.skills_dir = skills_dir or Path(__file__).resolve().parents[2] / "data" / "skills"

    def _parse_file(self, raw: str) -> dict[str, Any] | None:
        """Parse a markdown file with YAML frontmatter.

        Args:
            raw: The raw markdown content with YAML frontmatter.

        Returns:
            Parsed skill dict with keys ``name``, ``description``, ``domain``,
            ``tags``, ``content``, or ``None`` if the frontmatter is invalid.
        """
        if not raw.startswith("---"):
            return None

        # Find the closing ---
        second_sep = raw.find("---", 3)
        if second_sep == -1:
            return None

        frontmatter_str = raw[3:second_sep].strip()
        content = raw[second_sep + 3 :].strip()

        try:
            meta = yaml.safe_load(frontmatter_str)
        except yaml.YAMLError:
            return None

        if not isinstance(meta, dict):
            return None

        name = meta.get("name")
        description = meta.get("description")
        if not name or not description:
            return None

        return {
            "name": str(name),
            "description": str(description),
            "domain": meta.get("domain"),
            "tags": meta.get("tags") or [],
            "content": content,
        }

    def _read_skill_file(self, path: Path) -> dict[str, Any] | None:
        """Read and parse a single skill file.

        Args:
            path: Absolute path to the skill file.

        Returns:
            Parsed skill dict, or ``None`` if the file is missing or invalid.
        """
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            return None

        return self._parse_file(raw)

    def list_skills(self, domain: str | None = None) -> list[dict[str, Any]]:
        """List skills filtered by domain.

        Args:
            domain: If ``None``, return all skills (global and domain-specific).
                If set, return only skills matching that domain.

        Returns:
            List of parsed skill dicts.
        """
        if not self.skills_dir.exists():
            return []

        results: list[dict[str, Any]] = []
        for path in sorted(self.skills_dir.glob("*.md")):
            skill = self._read_skill_file(path)
            if skill is None:
                continue

            if domain is not None:
                skill_domain = skill.get("domain")
                if skill_domain != domain:
                    continue

            results.append(skill)

        return results

    def list_all_skills(self) -> list[dict[str, Any]]:
        """List all skills regardless of domain.

        Returns:
            List of all parsed skill dicts (global and domain-specific).
        """
        if not self.skills_dir.exists():
            return []

        results: list[dict[str, Any]] = []
        for path in sorted(self.skills_dir.glob("*.md")):
            skill = self._read_skill_file(path)
            if skill is not None:
                results.append(skill)
        return results

    def get_skill(self, name: str) -> dict[str, Any] | None:
        """Get a single skill by name.

        Args:
            name: The skill name (filename without .md extension).

        Returns:
            Parsed skill dict, or ``None`` if not found.
        """
        path = self.skills_dir / f"{name}.md"
        return self._read_skill_file(path)

    def create_skill(
        self,
        name: str,
        description: str,
        content: str,
        domain: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new skill file.

        Args:
            name: Skill identifier (used as filename).
            description: Short description of the skill.
            content: Full prompt content (markdown body).
            domain: Optional domain (e.g. ``chapter``, ``plot``).
            tags: Optional list of tags.

        Returns:
            The created skill dict.

        Raises:
            ValueError: If a skill with the same name already exists.
        """
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        path = self.skills_dir / f"{name}.md"

        if path.exists():
            raise ValueError(f"Skill '{name}' already exists")

        tags = tags or []
        frontmatter = yaml.dump(
            {"name": name, "description": description, "domain": domain, "tags": tags},
            default_flow_style=True,
            allow_unicode=True,
        )
        raw = f"---\n{frontmatter}---\n\n{content}\n"
        path.write_text(raw, encoding="utf-8")

        return {
            "name": name,
            "description": description,
            "domain": domain,
            "tags": tags,
            "content": content,
        }

    def update_skill(self, name: str, **kwargs: Any) -> dict[str, Any] | None:
        """Update an existing skill.

        Args:
            name: Skill identifier.
            **kwargs: Fields to update. Supported: ``description``, ``content``,
                ``domain``, ``tags``.

        Returns:
            Updated skill dict, or ``None`` if not found.
        """
        supported = {"description", "content", "domain", "tags"}
        unknown = set(kwargs.keys()) - supported
        if unknown:
            raise ValueError(f"Unknown fields: {unknown}")

        existing = self.get_skill(name)
        if existing is None:
            return None

        # Apply updates
        for key in ("description", "domain", "tags"):
            if key in kwargs:
                existing[key] = kwargs[key]
        if "content" in kwargs:
            existing["content"] = kwargs["content"]

        # Write back
        frontmatter = yaml.dump(
            {
                "name": existing["name"],
                "description": existing["description"],
                "domain": existing["domain"],
                "tags": existing["tags"],
            },
            default_flow_style=True,
            allow_unicode=True,
        )
        raw = f"---\n{frontmatter}---\n\n{existing['content']}\n"
        path = self.skills_dir / f"{name}.md"
        path.write_text(raw, encoding="utf-8")

        return existing

    def delete_skill(self, name: str) -> bool:
        """Delete a skill file.

        Args:
            name: Skill identifier.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        path = self.skills_dir / f"{name}.md"
        if not path.exists():
            return False

        path.unlink()
        return True
