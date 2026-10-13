import re
from dataclasses import dataclass
from pathlib import Path

import yaml

GUIDE_NAMES = ("AGENT.md", "AGENTS.md", "CLAUDE.md")
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)
MAX_GUIDE_CHARS = 8000
MAX_SKILLS = 3


@dataclass(frozen=True)
class Skill:
    name: str
    triggers: tuple[str, ...]
    body: str

    def score(self, text: str) -> int:
        return sum(1 for trigger in self.triggers if re.search(rf"\b{re.escape(trigger)}\b", text))


def parse_skill(path: Path) -> Skill | None:
    match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        return None
    meta = yaml.safe_load(match.group(1)) or {}
    return Skill(
        name=meta.get("name", path.parent.name),
        triggers=tuple(str(trigger).lower() for trigger in meta.get("triggers", [])),
        body=match.group(2).strip(),
    )


class KnowledgeBase:
    def __init__(self, workspace: Path, skills_dirs: list[Path]):
        self.workspace = workspace
        self.skills = self._load_skills(skills_dirs)

    @staticmethod
    def _load_skills(skills_dirs: list[Path]) -> list[Skill]:
        by_name = {}
        for folder in skills_dirs:
            if not folder.is_dir():
                continue
            for path in sorted(folder.glob("*/SKILL.md")):
                skill = parse_skill(path)
                if skill:
                    by_name[skill.name] = skill
        return list(by_name.values())

    def project_guide(self) -> str:
        for name in GUIDE_NAMES:
            path = self.workspace / name
            if path.is_file():
                return path.read_text(encoding="utf-8")[:MAX_GUIDE_CHARS]
        return ""

    def relevant_skills(self, request: str) -> list[Skill]:
        text = request.lower()
        scored = [(skill.score(text), skill) for skill in self.skills]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [skill for score, skill in scored if score > 0][:MAX_SKILLS]

    def build_context(self, request: str) -> tuple[str, list[str]]:
        skills = self.relevant_skills(request)
        sections = []
        guide = self.project_guide()
        if guide:
            sections.append(f"# Project guide\n{guide}")
        sections.extend(f"# Skill: {skill.name}\n{skill.body}" for skill in skills)
        return "\n\n".join(sections), [skill.name for skill in skills]
