from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib import error, request

from flask import Flask, jsonify, render_template, request as flask_request

from api import RoverStore

app = Flask(__name__, template_folder="templates", static_folder="static")
store = RoverStore()


def _normalize_ip(ip_address: str) -> str:
    value = (ip_address or "").strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value.rstrip("/")
    return f"http://{value.rstrip('/')}"


def _forward_json(method: str, url: str, payload: dict | None = None) -> tuple[dict | None, str | None]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url=url, data=data, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=1.5) as resp:
            raw = resp.read().decode("utf-8")
            return (json.loads(raw) if raw else {}), None
    except error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except error.URLError as exc:
        return None, str(exc.reason)
    except (TimeoutError, json.JSONDecodeError):
        return None, "timeout or bad response"


def _check_rover_connection(rover_id: str, ip_address: str) -> tuple[bool, dict | None, str | None]:
    status, err = _forward_json("GET", f"{ip_address}/status")
    checked_at = datetime.now(timezone.utc).isoformat()
    if isinstance(status, dict):
        store.upsert_status(rover_id, status, ip_address=ip_address)
        store.update_connection(rover_id, online=True, checked_at=checked_at)
        return True, status, None
    store.update_connection(rover_id, online=False, checked_at=checked_at, error_message=err)
    return False, None, err


@app.get("/")
def dashboard():
    return render_template("dashboard.html")


@app.get("/rovers")
def list_rovers():
    return jsonify({"items": store.list_rovers()})


@app.post("/rovers")
def create_rover():
    payload = flask_request.get_json(silent=True) or {}
    rover_id = (payload.get("id") or "").strip()
    ip_address = _normalize_ip(payload.get("ip_address") or "") or None
    if not rover_id:
        return jsonify({"ok": False, "error": "id is required"}), 400
    rover = store.create_rover(rover_id, ip_address=ip_address)
    return jsonify({"ok": True, "item": rover})


@app.post("/rovers/connect")
def connect_rover():
    payload = flask_request.get_json(force=True)
    rover_id = (payload.get("id") or "").strip()
    ip_address = _normalize_ip(payload.get("ip_address") or "")
    if not rover_id or not ip_address:
        return jsonify({"ok": False, "error": "id and ip_address are required"}), 400

    rover = store.create_rover(rover_id, ip_address=ip_address)
    connected, _, err = _check_rover_connection(rover_id, ip_address)
    rover = store.get_rover(rover_id) or rover
    return jsonify({"ok": True, "item": rover, "connected": connected, "error": err})


@app.post("/rovers/<rover_id>/check_connection")
def check_connection(rover_id: str):
    rover = store.get_rover(rover_id)
    ip_address = _normalize_ip(rover.get("ip_address") or "")
    if not ip_address:
        return jsonify({"ok": False, "connected": False, "error": "ip_address not configured"}), 400
    connected, _, err = _check_rover_connection(rover_id, ip_address)
    return jsonify({"ok": True, "connected": connected, "error": err, "item": store.get_rover(rover_id)})


@app.get("/rovers/<rover_id>/status")
def rover_status(rover_id: str):
    rover = store.get_rover(rover_id)
    ip_address = rover.get("ip_address")
    if ip_address:
        _check_rover_connection(rover_id, ip_address)
        rover = store.get_rover(rover_id)
    return jsonify(rover)


@app.post("/rovers/<rover_id>/status")
def push_status(rover_id: str):
    payload = flask_request.get_json(force=True)
    ip_address = _normalize_ip(payload.get("ip_address") or "") or None
    store.upsert_status(rover_id, payload, ip_address=ip_address)
    return jsonify({"ok": True})


@app.get("/rovers/<rover_id>/commands")
def rover_commands(rover_id: str):
    return jsonify({"items": store.pop_commands(rover_id)})


@app.post("/rovers/<rover_id>/command")
def rover_command(rover_id: str):
    payload = flask_request.get_json(force=True)
    store.enqueue_command(rover_id, payload)

    rover = store.get_rover(rover_id)
    ip_address = rover.get("ip_address")
    forwarded = False
    if ip_address:
        response, _ = _forward_json("POST", f"{ip_address}/command", payload)
        forwarded = response is not None

    return jsonify({"ok": True, "forwarded": forwarded})


@app.post("/rovers/<rover_id>/goal")
def rover_goal(rover_id: str):
    payload = flask_request.get_json(force=True)
    store.set_goal(rover_id, payload)
    store.enqueue_command(rover_id, {"type": "route", "payload": payload})

    rover = store.get_rover(rover_id)
    ip_address = rover.get("ip_address")
    forwarded = False
    if ip_address:
        response, _ = _forward_json("POST", f"{ip_address}/goal", payload)
        forwarded = response is not None

    return jsonify({"ok": True, "forwarded": forwarded})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
