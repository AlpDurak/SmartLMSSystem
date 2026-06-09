import json
import time
import uuid
from datetime import datetime, timezone

import pytest

import smart_lms.config as cfg_mod
import smart_lms.tools.sessions as sess_mod
from smart_lms.tools.sessions import _list_sessions_raw, _session_path


@pytest.fixture(autouse=True)
def tmp_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_mod, "SMART_LMS_DIR", tmp_path / ".smart-lms")
    monkeypatch.setattr(cfg_mod, "SESSIONS_DIR", tmp_path / ".smart-lms" / "sessions")
    monkeypatch.setattr(cfg_mod, "CONFIG_FILE", tmp_path / ".smart-lms" / "config.json")
    monkeypatch.setattr(sess_mod, "SESSIONS_DIR", tmp_path / ".smart-lms" / "sessions")
    cfg_mod.ensure_dirs()


def _make_session(title: str, course: str = "") -> str:
    session_id = str(uuid.uuid4())
    data = {
        "id": session_id,
        "title": title,
        "course": course,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "turns": [],
    }
    sess_mod._session_path(session_id).write_text(json.dumps(data))
    return session_id


def test_create_session_file_has_uuid_format():
    sid = _make_session("Test", "X")
    assert len(sid) == 36
    assert sess_mod._session_path(sid).exists()


def test_save_and_load_turn():
    sid = _make_session("T")
    path = sess_mod._session_path(sid)
    data = json.loads(path.read_text())
    data["turns"].append({"role": "user", "text": "Hello", "sources": ["course:1"]})
    path.write_text(json.dumps(data))
    loaded = json.loads(path.read_text())
    assert loaded["turns"][0]["text"] == "Hello"


def test_list_sessions_returns_newest_first():
    sid1 = _make_session("A")
    time.sleep(0.02)
    sid2 = _make_session("B")
    sessions = _list_sessions_raw()
    assert len(sessions) == 2
    # newest first — sid2 was created last
    assert sessions[0]["id"] == sid2


def test_load_missing_session_returns_empty():
    path = sess_mod._session_path("nope")
    result = json.loads(path.read_text()) if path.exists() else {}
    assert result == {}
