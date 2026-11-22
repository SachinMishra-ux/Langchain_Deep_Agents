"""Skill discovery and loading for LocData Code."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from locdata_code.paths import get_skills_dirs


@dataclass
class Skill:
    """Represents a discovered LocData skill."""

    name: str
    description: str
    instructions: str
    path: Path


class SkillManager:
    """Manages discovery and access to custom skills."""

    @classmethod
    def parse_skill_file(cls, skill_path: Path) -> Skill | None:
        """Parse a SKILL.md file with YAML frontmatter."""
        try:
            content = skill_path.read_text(encoding="utf-8")
            # Parse YAML frontmatter --- ... ---
            match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
            name = skill_path.parent.name
            description = "Custom skill"
            instructions = content

            if match:
                frontmatter, body = match.groups()
                instructions = body.strip()
                for line in frontmatter.splitlines():
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip().strip('"\'')
                    elif line.startswith("description:"):
                        description = line.split(":", 1)[1].strip().strip('"\'')

            return Skill(
                name=name,
                description=description,
                instructions=instructions,
                path=skill_path,
            )
        except Exception:
            return None

    @classmethod
    def discover_skills(cls, project_root: str | Path | None = None) -> list[Skill]:
        """Scan skills directories for SKILL.md files."""
        skills: list[Skill] = []
        for sdir in get_skills_dirs(project_root):
            for skill_file in sdir.glob("**/SKILL.md"):
                parsed = cls.parse_skill_file(skill_file)
                if parsed:
                    skills.append(parsed)
        return skills

    @classmethod
    def format_skills_prompt(cls, skills: list[Skill]) -> str:
        """Format discovered skills for inclusion in agent prompt or discovery list."""
        if not skills:
            return ""
        lines = ["\n### AVAILABLE SKILLS:"]
        for s in skills:
            lines.append(f"- **{s.name}**: {s.description}")
        return "\n".join(lines)
