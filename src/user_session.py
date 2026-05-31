"""
User Session Manager - ACC WhatsApp Bot
Persistent session per nomor HP, tersimpan di data/sessions/users.json
"""
import json
import threading
from pathlib import Path
from datetime import datetime


class UserSession:
    """Sesi per pengguna WhatsApp."""

    def __init__(self, phone: str):
        self.phone = phone
        self.name = ""
        self.plan = "free"          # free | pro | admin
        self.model_key = "claude-sonnet"
        self.model_config = {
            "provider": "anthropic",
            "model": "claude-sonnet-4-5",
        }
        self.skill = None            # nama skill aktif, None = mode umum
        self.history: list = []      # [{"role": "user"|"assistant", "content": "..."}]
        self.pending = None          # untuk stateful menu (belum dipakai)
        self.registered_at = datetime.now().isoformat()
        self.last_active = datetime.now().isoformat()

    # ── Serialisasi ────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "phone": self.phone,
            "name": self.name,
            "plan": self.plan,
            "model_key": self.model_key,
            "model_config": self.model_config,
            "skill": self.skill,
            "history": self.history[-40:],  # simpan 20 pasang terakhir
            "pending": self.pending,
            "registered_at": self.registered_at,
            "last_active": self.last_active,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "UserSession":
        s = cls(d["phone"])
        s.name = d.get("name", "")
        s.plan = d.get("plan", "free")
        s.model_key = d.get("model_key", "claude-sonnet")
        s.model_config = d.get("model_config", {
            "provider": "anthropic", "model": "claude-sonnet-4-5"
        })
        s.skill = d.get("skill")
        s.history = d.get("history", [])
        s.pending = d.get("pending")
        s.registered_at = d.get("registered_at", datetime.now().isoformat())
        s.last_active = d.get("last_active", datetime.now().isoformat())
        return s

    # ── Helper ──────────────────────────────────────────────────
    def message_count(self) -> int:
        """Jumlah pasang pesan (user + assistant)."""
        return len(self.history) // 2

    def last_ai_response(self) -> str | None:
        """Respons AI terakhir."""
        for m in reversed(self.history):
            if m.get("role") == "assistant":
                return m.get("content")
        return None

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > 40:
            self.history = self.history[-40:]


class SessionManager:
    """Thread-safe persistent session manager."""

    def __init__(self, data_dir: Path):
        self._file = data_dir / "sessions" / "users.json"
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._cache: dict[str, UserSession] = {}
        self._load()

    # ── Persistensi ────────────────────────────────────────────
    def _load(self):
        if not self._file.exists():
            return
        try:
            raw = json.loads(self._file.read_text("utf-8"))
            for phone, d in raw.items():
                self._cache[phone] = UserSession.from_dict(d)
        except Exception:
            pass  # file corrupt → mulai fresh

    def _save(self):
        data = {phone: s.to_dict() for phone, s in self._cache.items()}
        self._file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ── API ────────────────────────────────────────────────────
    def get(self, phone: str, name: str = "") -> UserSession:
        """Ambil atau buat sesi untuk nomor HP."""
        with self._lock:
            if phone not in self._cache:
                s = UserSession(phone)
                s.name = name
                self._cache[phone] = s
                self._save()
            else:
                if name and not self._cache[phone].name:
                    self._cache[phone].name = name
            self._cache[phone].last_active = datetime.now().isoformat()
            return self._cache[phone]

    def save(self, session: UserSession):
        """Simpan sesi ke disk."""
        with self._lock:
            self._cache[session.phone] = session
            self._save()

    def reset(self, phone: str):
        """Hapus riwayat percakapan, pertahankan pengaturan model & skill."""
        with self._lock:
            if phone in self._cache:
                s = self._cache[phone]
                s.history = []
                s.pending = None
                self._save()

    def add_message(self, phone: str, role: str, content: str):
        """Tambah pesan ke riwayat dan simpan."""
        with self._lock:
            if phone in self._cache:
                self._cache[phone].add_message(role, content)
                self._save()

    def active_count(self) -> int:
        with self._lock:
            return len(self._cache)

    def all_users(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "phone": s.phone,
                    "name": s.name,
                    "plan": s.plan,
                    "model": s.model_key,
                    "skill": s.skill,
                    "messages": s.message_count(),
                    "last_active": s.last_active[:16],
                }
                for s in self._cache.values()
            ]
