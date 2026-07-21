"""Tests for SkillService (CRUD + frontmatter parsing)."""

from pathlib import Path

import pytest

from app.services.skill import SkillService


class TestParseFrontmatter:
    """Verify _parse_file frontmatter parsing logic."""

    def test_valid_frontmatter(self, tmp_path: Path) -> None:
        """Valid frontmatter with all fields returns parsed dict."""
        svc = SkillService(skills_dir=tmp_path)
        raw = (
            "---\nname: wuxia-writing\ndescription: 金庸武侠小说写作风格\n"
            "domain: chapter\ntags: [武侠, 写作风格]\n---\n\n正文内容"
        )
        result = svc._parse_file(raw)
        assert result is not None
        assert result["name"] == "wuxia-writing"
        assert result["description"] == "金庸武侠小说写作风格"
        assert result["domain"] == "chapter"
        assert result["tags"] == ["武侠", "写作风格"]
        assert result["content"] == "正文内容"

    def test_no_frontmatter_returns_none(self, tmp_path: Path) -> None:
        """A file without frontmatter returns None."""
        svc = SkillService(skills_dir=tmp_path)
        result = svc._parse_file("no frontmatter here")
        assert result is None

    def test_missing_name_returns_none(self, tmp_path: Path) -> None:
        """Frontmatter missing name field returns None."""
        svc = SkillService(skills_dir=tmp_path)
        raw = "---\ndescription: some desc\n---\n\ncontent"
        result = svc._parse_file(raw)
        assert result is None

    def test_missing_description_returns_none(self, tmp_path: Path) -> None:
        """Frontmatter missing description field returns None."""
        svc = SkillService(skills_dir=tmp_path)
        raw = "---\nname: test\n---\n\ncontent"
        result = svc._parse_file(raw)
        assert result is None

    def test_no_domain_is_none(self, tmp_path: Path) -> None:
        """When domain is absent in frontmatter, parsed dict has domain=None."""
        svc = SkillService(skills_dir=tmp_path)
        raw = "---\nname: global-skill\ndescription: a global skill\n---\n\nbody"
        result = svc._parse_file(raw)
        assert result is not None
        assert result["domain"] is None

    def test_empty_tags_is_empty_list(self, tmp_path: Path) -> None:
        """When tags is absent in frontmatter, parsed dict has tags=[]."""
        svc = SkillService(skills_dir=tmp_path)
        raw = "---\nname: no-tags\ndescription: skill without tags\n---\n\nbody"
        result = svc._parse_file(raw)
        assert result is not None
        assert result["tags"] == []

    def test_malformed_yaml_returns_none(self, tmp_path: Path) -> None:
        """Malformed YAML in frontmatter returns None."""
        svc = SkillService(skills_dir=tmp_path)
        raw = "---\n: invalid:\n  yaml:\n---\n\nbody"
        result = svc._parse_file(raw)
        assert result is None


class TestListSkills:
    """Verify list_skills filtering logic."""

    def test_empty_dir_returns_empty_list(self, tmp_path: Path) -> None:
        """An empty skills directory returns an empty list."""
        svc = SkillService(skills_dir=tmp_path)
        assert svc.list_skills() == []

    def test_no_domain_returns_all(self, tmp_path: Path) -> None:
        """list_skills(domain=None) returns all skills (global and domain-specific)."""
        svc = SkillService(skills_dir=tmp_path)
        # Global skill (no domain)
        (tmp_path / "global.md").write_text(
            "---\nname: global\ndescription: global skill\n---\n\nbody", encoding="utf-8"
        )
        # Domain skill
        (tmp_path / "chapter.md").write_text(
            "---\nname: chapter\ndescription: chapter skill\ndomain: chapter\n---\n\nbody", encoding="utf-8"
        )
        result = svc.list_skills()
        assert len(result) == 2
        names = {r["name"] for r in result}
        assert names == {"global", "chapter"}

    def test_domain_filtering(self, tmp_path: Path) -> None:
        """list_skills(domain='chapter') returns only skills with that domain."""
        svc = SkillService(skills_dir=tmp_path)
        (tmp_path / "global.md").write_text(
            "---\nname: global\ndescription: global skill\n---\n\nbody", encoding="utf-8"
        )
        (tmp_path / "chapter.md").write_text(
            "---\nname: chapter\ndescription: chapter skill\ndomain: chapter\n---\n\nbody", encoding="utf-8"
        )
        (tmp_path / "plot.md").write_text(
            "---\nname: plot\ndescription: plot skill\ndomain: plot\n---\n\nbody", encoding="utf-8"
        )
        result = svc.list_skills(domain="chapter")
        assert len(result) == 1
        assert result[0]["name"] == "chapter"

    def test_ignores_invalid_files(self, tmp_path: Path) -> None:
        """Invalid files (no frontmatter) are silently skipped."""
        svc = SkillService(skills_dir=tmp_path)
        (tmp_path / "good.md").write_text("---\nname: good\ndescription: valid\n---\n\nbody", encoding="utf-8")
        (tmp_path / "bad.md").write_text("no frontmatter", encoding="utf-8")
        result = svc.list_skills()
        assert len(result) == 1
        assert result[0]["name"] == "good"


class TestGetSkill:
    """Verify get_skill by name."""

    def test_get_existing_skill(self, tmp_path: Path) -> None:
        """Get an existing skill by name returns its dict."""
        svc = SkillService(skills_dir=tmp_path)
        (tmp_path / "wuxia.md").write_text(
            "---\nname: wuxia\ndescription: wuxia writing\n---\n\ncontent here", encoding="utf-8"
        )
        result = svc.get_skill("wuxia")
        assert result is not None
        assert result["name"] == "wuxia"
        assert result["content"] == "content here"

    def test_get_nonexistent_returns_none(self, tmp_path: Path) -> None:
        """Getting a nonexistent skill returns None."""
        svc = SkillService(skills_dir=tmp_path)
        assert svc.get_skill("nonexistent") is None


class TestCreateSkill:
    """Verify create_skill behaviour."""

    def test_create_new_skill(self, tmp_path: Path) -> None:
        """Creating a new skill writes the file and returns parsed dict."""
        svc = SkillService(skills_dir=tmp_path)
        result = svc.create_skill("wuxia", "武侠写作风格", "正文内容", domain="chapter", tags=["武侠"])
        assert result["name"] == "wuxia"
        assert result["description"] == "武侠写作风格"
        assert result["domain"] == "chapter"
        assert result["tags"] == ["武侠"]
        assert result["content"] == "正文内容"
        # Verify file exists
        assert (tmp_path / "wuxia.md").exists()

    def test_create_global_skill(self, tmp_path: Path) -> None:
        """Creating a skill with domain=None writes correctly."""
        svc = SkillService(skills_dir=tmp_path)
        result = svc.create_skill("global", "全局技能", "内容")
        assert result["domain"] is None
        assert result["tags"] == []

    def test_create_duplicate_raises_value_error(self, tmp_path: Path) -> None:
        """Creating a skill that already exists raises ValueError."""
        svc = SkillService(skills_dir=tmp_path)
        svc.create_skill("dup", "first", "content")
        with pytest.raises(ValueError, match="already exists"):
            svc.create_skill("dup", "second", "content2")

    def test_create_creates_parent_directories(self, tmp_path: Path) -> None:
        """Creating a skill in a non-existent nested dir creates it."""
        nested = tmp_path / "sub" / "skills"
        svc = SkillService(skills_dir=nested)
        result = svc.create_skill("new", "new skill", "body")
        assert result["name"] == "new"
        assert (nested / "new.md").exists()


class TestUpdateSkill:
    """Verify update_skill behaviour."""

    def test_update_description(self, tmp_path: Path) -> None:
        """Updating description modifies the file."""
        svc = SkillService(skills_dir=tmp_path)
        svc.create_skill("test", "original", "body")
        result = svc.update_skill("test", description="updated description")
        assert result is not None
        assert result["description"] == "updated description"
        # Verify persistence
        persisted = svc.get_skill("test")
        assert persisted is not None
        assert persisted["description"] == "updated description"

    def test_update_content(self, tmp_path: Path) -> None:
        """Updating content modifies the file body."""
        svc = SkillService(skills_dir=tmp_path)
        svc.create_skill("test", "desc", "old body")
        result = svc.update_skill("test", content="new body")
        assert result is not None
        assert result["content"] == "new body"

    def test_update_nonexistent_returns_none(self, tmp_path: Path) -> None:
        """Updating a nonexistent skill returns None."""
        svc = SkillService(skills_dir=tmp_path)
        assert svc.update_skill("nope", description="x") is None

    def test_update_unknown_field_raises(self, tmp_path: Path) -> None:
        """Updating with an unknown field raises ValueError."""
        svc = SkillService(skills_dir=tmp_path)
        svc.create_skill("test", "desc", "body")
        with pytest.raises(ValueError, match="Unknown fields"):
            svc.update_skill("test", typo_field="bar")


class TestDeleteSkill:
    """Verify delete_skill behaviour."""

    def test_delete_existing_returns_true(self, tmp_path: Path) -> None:
        """Deleting an existing skill returns True and removes the file."""
        svc = SkillService(skills_dir=tmp_path)
        svc.create_skill("doomed", "to be deleted", "body")
        assert svc.delete_skill("doomed") is True
        assert svc.get_skill("doomed") is None

    def test_delete_nonexistent_returns_false(self, tmp_path: Path) -> None:
        """Deleting a nonexistent skill returns False."""
        svc = SkillService(skills_dir=tmp_path)
        assert svc.delete_skill("ghost") is False
