"""数据存储"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class Database:
    def __init__(self, path: str = "data"):
        self.path = path
        os.makedirs(path, exist_ok=True)

    def _get_file(self, name: str) -> str:
        return os.path.join(self.path, f"{name}.json")

    def load(self, name: str) -> List[Dict]:
        path = self._get_file(name)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return []

    def save(self, name: str, data: List[Dict]):
        with open(self._get_file(name), 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

class SessionStore:
    def __init__(self, db: Database):
        self.db = db
        self.sessions: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        for s in self.db.load("sessions"):
            self.sessions[s["id"]] = s

    def get(self, session_id: str) -> Optional[Dict]:
        return self.sessions.get(session_id)

    def save(self, session: Dict):
        session["updated_at"] = datetime.now().isoformat()
        self.sessions[session["id"]] = session
        self.db.save("sessions", list(self.sessions.values()))

class MessageStore:
    def __init__(self, db: Database):
        self.db = db
        self.messages: List[Dict] = self.db.load("messages")

    def save(self, message: Dict):
        self.messages.append(message)
        if len(self.messages) > 10000:
            self.messages = self.messages[-5000:]
        self.db.save("messages", self.messages)

    def save_response(self, response: Dict):
        self.messages.append({"type": "response", **response})
        self.db.save("messages", self.messages)

    def get_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        return [m for m in self.messages if m.get("session_id") == session_id][-limit:]
