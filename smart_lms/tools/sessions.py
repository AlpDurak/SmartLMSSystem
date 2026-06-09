import json
import uuid
from datetime import datetime, timezone
from fastmcp import FastMCP
from smart_lms.config import SESSIONS_DIR, ensure_dirs


def _session_path(session_id: str):
    return SESSIONS_DIR / f"{session_id}.json"


def _list_sessions_raw() -> list[dict]:
    """Internal helper used by ui_bridge API route."""
    ensure_dirs()
    sessions = []
    for p in sorted(SESSIONS_DIR.glob("*.json"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True):
        try:
            data = json.loads(p.read_text())
            sessions.append({
                "id": data["id"],
                "title": data.get("title", "Untitled"),
                "course": data.get("course", ""),
                "created_at": data.get("created_at", ""),
                "turn_count": len(data.get("turns", [])),
            })
        except Exception:
            continue
    return sessions


def register_session_tools(mcp: FastMCP):

    @mcp.tool()
    def create_session(title: str, course: str = "") -> str:
        """Create a new study session. Returns session_id."""
        ensure_dirs()
        session_id = str(uuid.uuid4())
        data = {
            "id": session_id,
            "title": title,
            "course": course,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "turns": [],
        }
        _session_path(session_id).write_text(json.dumps(data, indent=2))
        return session_id

    @mcp.tool()
    def save_turn(session_id: str, role: str, text: str,
                  sources: list[str],
                  blocks: list[dict] | None = None) -> str:
        """Append a turn to a session. role: 'user'|'assistant'. Returns session_id."""
        path = _session_path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"Session {session_id} not found")
        data = json.loads(path.read_text())
        turn = {"role": role, "text": text, "sources": sources}
        if blocks:
            turn["blocks"] = blocks
        data["turns"].append(turn)
        path.write_text(json.dumps(data, indent=2))
        return session_id

    @mcp.tool()
    def list_sessions() -> list[dict]:
        """List all study sessions, newest first."""
        return _list_sessions_raw()

    @mcp.tool()
    def load_session(session_id: str) -> dict:
        """Load a full session including all turns."""
        path = _session_path(session_id)
        if not path.exists():
            return {}
        return json.loads(path.read_text())
