import re

from aipilot.llm.client import complete
from aipilot.llm.registry import ModelRegistry

KINDS = ("chat", "coding", "design", "complex")

CLASSIFIER_PROMPT = """Classify the user's request for a coding assistant. Reply with exactly one word:

chat - questions, explanations, suggestions, small talk, no code changes needed
coding - write, fix, review, test or explain specific code, a bug, or a small feature
design - UI/UX, layout, styling, visual design, landing pages, design systems
complex - architecture, whole projects, multi-file features, migrations, building apps from scratch"""

CODING_WORDS = re.compile(
    r"\b(code|bug|error|fix|function|class|api|endpoint|test|tests|refactor|implement|script|"
    r"install|deploy|docker|python|javascript|typescript|react|node|electron|django|fastapi|"
    r"sql|git|file|repo|build|compile|traceback|exception)\b",
    re.IGNORECASE,
)
DESIGN_WORDS = re.compile(
    r"\b(design|ui|ux|layout|landing page|figma|tailwind|css|theme|animation|mockup|wireframe)\b",
    re.IGNORECASE,
)
COMPLEX_WORDS = re.compile(
    r"\b(architecture|entire|whole|full|from scratch|end to end|migrate|monorepo|project|system)\b",
    re.IGNORECASE,
)


def heuristic_kind(request: str) -> str:
    if COMPLEX_WORDS.search(request) and CODING_WORDS.search(request):
        return "complex"
    if DESIGN_WORDS.search(request):
        return "design"
    if CODING_WORDS.search(request):
        return "coding"
    return "chat"


async def classify_request(registry: ModelRegistry, request: str) -> str:
    messages = [
        {"role": "system", "content": CLASSIFIER_PROMPT},
        {"role": "user", "content": request},
    ]
    try:
        _, reply = await complete(registry.candidates("classify"), messages)
    except Exception:
        return heuristic_kind(request)
    words = re.findall(r"[a-z]+", reply["content"].lower())
    return next((word for word in words if word in KINDS), heuristic_kind(request))
