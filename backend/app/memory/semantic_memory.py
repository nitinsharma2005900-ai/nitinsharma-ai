import json
import re
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.schemas.memory import MemoryItem


# Pattern matchers for extracting user preferences, styles, and background facts
PREFERENCE_PATTERNS = [
    (r"(?:i work in|i code in|my (?:main|primary) language is)\s+([a-zA-Z\+\#]+)", "User works primarily in {match}"),
    (r"(?:prefer|like|want)\s+([a-zA-Z0-9\s,\-_]+(?:responses|answers|code|style))", "User preference: {match}"),
    (r"(?:prefer|want)\s+(brief[,\s]+code-only|code-only|concise|detailed|step-by-step)\s*(?:responses|answers)?", "User preference: {match} responses"),
    (r"(?:i am a|i'm a)\s+([a-zA-Z0-9\s]+(?:developer|engineer|scientist|student|analyst))", "User role: {match}"),
    (r"(?:call me|my name is)\s+([A-Z][a-zA-Z]+)", "User name: {match}"),
    (r"(?:do not include|no|avoid)\s+([a-zA-Z0-9\s]+(?:explanations|fluff|intro|filler))", "User restriction: Avoid {match}"),
]


class SemanticMemoryStore:
    """
    Persistent semantic memory store implementing Mem0 integration
    and local persistent disk-backed semantic memory.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or settings.MEMORY_STORE_PATH
        self.memories: Dict[str, List[Dict[str, Any]]] = {}
        self.mem0_client = None
        self._init_mem0_if_available()
        self.load()

    def _init_mem0_if_available(self):
        """Attempts to initialize Mem0 client if MEM0_API_KEY is configured."""
        if settings.MEM0_API_KEY and not settings.OFFLINE_TEST_MODE:
            try:
                from mem0 import Memory
                self.mem0_client = Memory()
            except Exception:
                self.mem0_client = None

    def extract_facts_from_text(self, text: str) -> List[str]:
        """
        Extracts semantic facts, preferences, and persona details from user input.
        Extracts specific facts like preferred languages and response styles.
        """
        extracted: List[str] = []
        lower_text = text.lower().strip()

        # Check for programming language / tech stack mentions
        lang_matches = re.findall(
            r"\b(python|javascript|typescript|c\+\+|golang|rust|java|ruby|php|sql|scala)\b",
            lower_text
        )
        if "work in" in lower_text or "code in" in lower_text or "develop in" in lower_text or "use" in lower_text:
            for lang in set(lang_matches):
                extracted.append(f"User works in {lang.title()} and prefers {lang.title()} code solutions.")

        # Check for response style preferences
        if "brief" in lower_text and ("code-only" in lower_text or "code only" in lower_text):
            extracted.append("User prefers brief, code-only responses without unnecessary explanations.")
        elif "code-only" in lower_text or "code only" in lower_text:
            extracted.append("User prefers code-only responses without commentary.")
        elif "brief" in lower_text or "concise" in lower_text:
            extracted.append("User prefers concise, brief answers.")
        elif "detailed" in lower_text or "step-by-step" in lower_text:
            extracted.append("User prefers in-depth, step-by-step explanations.")

        # Pattern-based extraction
        for pattern, template in PREFERENCE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                matched_str = m.group(1).strip()
                fact = template.format(match=matched_str)
                if fact not in extracted:
                    extracted.append(fact)

        return extracted

    def add_memory(self, user_id: str, fact: str, category: str = "preference") -> MemoryItem:
        """Adds a single memory fact for a user and persists to disk."""
        if user_id not in self.memories:
            self.memories[user_id] = []

        # Avoid exact duplicate facts
        for existing in self.memories[user_id]:
            if existing["fact"].lower() == fact.lower():
                return MemoryItem(**existing)

        mem_id = f"mem_{uuid.uuid4().hex[:10]}"
        item = {
            "id": mem_id,
            "user_id": user_id,
            "fact": fact,
            "category": category,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        self.memories[user_id].append(item)
        self.save()

        # Sync to Mem0 cloud if client is configured
        if self.mem0_client:
            try:
                self.mem0_client.add(fact, user_id=user_id)
            except Exception:
                pass

        return MemoryItem(**item)

    def extract_and_store(self, user_id: str, text: str) -> List[str]:
        """Extracts facts from user query and stores new facts."""
        facts = self.extract_facts_from_text(text)
        newly_added: List[str] = []
        for f in facts:
            # Check if already saved
            existing_facts = [m["fact"].lower() for m in self.memories.get(user_id, [])]
            if f.lower() not in existing_facts:
                self.add_memory(user_id, f)
                newly_added.append(f)
        return newly_added

    def get_user_memories(self, user_id: str) -> List[MemoryItem]:
        """Returns all stored memories for a user."""
        items = self.memories.get(user_id, [])
        return [MemoryItem(**item) for item in items]

    def build_persona_prompt(self, user_id: str) -> str:
        """
        Retrieves user memories and generates a system prompt directive
        for persona adaptation.
        """
        user_mems = self.get_user_memories(user_id)
        if not user_mems:
            return ""

        facts_list = "\n".join(f"- {m.fact}" for m in user_mems)
        return (
            "\n[LONG-TERM USER SEMANTIC PROFILE & PREFERENCES]\n"
            f"{facts_list}\n"
            "INSTRUCTION: You MUST adapt your response to adhere strictly to the user preferences above. "
            "For instance, if the user requested brief or code-only answers, omit conversational filler "
            "and output only the requested code.\n"
        )

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Deletes a specific memory item by ID."""
        if user_id not in self.memories:
            return False
        initial_len = len(self.memories[user_id])
        self.memories[user_id] = [m for m in self.memories[user_id] if m["id"] != memory_id]
        if len(self.memories[user_id]) < initial_len:
            self.save()
            return True
        return False

    def clear_user_memories(self, user_id: str) -> int:
        """Clears all memories for a specific user."""
        count = len(self.memories.get(user_id, []))
        if user_id in self.memories:
            self.memories[user_id] = []
            self.save()
        return count

    def save(self):
        """Persists memories to JSON."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.memories, f, indent=2)

    def load(self):
        """Loads memories from JSON."""
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                self.memories = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load memories: {e}")
