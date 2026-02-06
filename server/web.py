from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from api import RoverStore

app = Flask(__name__, template_folder="templates", static_folder="static")
store = RoverStore()


@app.get("/")
def dashboard():
    return render_template("dashboard.html")


@app.get("/rovers")
def list_rovers():
    return jsonify({"items": store.list_rovers()})


@app.post("/rovers")
def create_rover():
    payload = request.get_json(silent=True) or {}
    rover_id = (payload.get("id") or "").strip()
    if not rover_id:
        return jsonify({"ok": False, "error": "id is required"}), 400
    rover = store.create_rover(rover_id)
    return jsonify({"ok": True, "item": rover})


@app.get("/rovers/<rover_id>/status")
def rover_status(rover_id: str):
    return jsonify(store.get_rover(rover_id))


@app.post("/rovers/<rover_id>/status")
def push_status(rover_id: str):
    payload = request.get_json(force=True)
    store.upsert_status(rover_id, payload)
    return jsonify({"ok": True})


@app.get("/rovers/<rover_id>/commands")
def rover_commands(rover_id: str):
    return jsonify({"items": store.pop_commands(rover_id)})


@app.post("/rovers/<rover_id>/command")
def rover_command(rover_id: str):
    payload = request.get_json(force=True)
    store.enqueue_command(rover_id, payload)
    return jsonify({"ok": True})


@app.post("/rovers/<rover_id>/goal")
def rover_goal(rover_id: str):
    payload = request.get_json(force=True)
    store.set_goal(rover_id, payload)
    store.enqueue_command(rover_id, {"type": "route", "payload": payload})
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
