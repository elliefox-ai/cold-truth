#!/usr/bin/env python3
"""
Cold Truth — Game Shell
Serves the detective game UI and API.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from case_generator import generate_case, TestCase, EvidenceType
import os
import random
import time

app = Flask(__name__, static_folder='.')
CORS(app)

# In-memory game state
current_case: TestCase | None = None
game_state = {
    "started": False,
    "found_clues": [],
    "reviewed_clues": [],  # clues the player has "reviewed" (reveals points_to)
    "interviewed": [],
    "notes": [],
    "accusation": None,
    "turn": 0,
}


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/new', methods=['POST'])
def new_game():
    global current_case, game_state
    data = request.json or {}
    seed = data.get('seed')
    current_case = generate_case(seed=seed)
    game_state = {
        "started": True,
        "found_clues": [],
        "reviewed_clues": [],
        "interviewed": [],
        "notes": [],
        "accusation": None,
        "turn": 0,
    }

    # Build suspect dialogue info for frontend
    suspects_data = []
    for s in current_case.suspects:
        suspects_data.append({
            "name": s.name,
            "role": s.role,
            "personality": s.personality,
            "relationship": s.relationship_to_victim,
            "dialogue": {
                "initial_statement": s.dialogue.initial_statement if s.dialogue else "",
                "follow_ups": [
                    {
                        "topic": fu.topic,
                        "requires_clue": fu.requires_clue,
                    }
                    for fu in (s.dialogue.follow_ups if s.dialogue else [])
                ],
            },
        })

    return jsonify({
        "victim": {
            "name": current_case.victim.name,
            "role": "victim",
        },
        "suspects": suspects_data,
        "crime_scene": current_case.crime_scene,
        "cause_of_death": current_case.cause_of_death.value,
        "num_clues": len(current_case.clues),
    })


@app.route('/api/investigate', methods=['POST'])
def investigate():
    """Search a location for clues."""
    if not current_case or not game_state["started"]:
        return jsonify({"error": "No active case"}), 400

    data = request.json or {}
    location = data.get("location", "").lower()

    found_ids = set(game_state["found_clues"])
    available = []

    for clue in current_case.clues:
        if clue.id in found_ids:
            continue
        if clue.location.lower() != location:
            continue
        if any(req not in found_ids for req in clue.requires):
            continue
        available.append(clue)

    if not available:
        locked = [c for c in current_case.clues
                  if c.id not in found_ids
                  and c.location.lower() == location
                  and any(req not in found_ids for req in c.requires)]
        if locked:
            hint = "You sense there's more to find here, but you need more evidence first."
        else:
            hint = None
        return jsonify({
            "found": False,
            "message": f"Nothing new found in {location}.",
            "hint": hint,
        })

    clue = available[0]
    game_state["found_clues"].append(clue.id)
    game_state["turn"] += 1

    # Don't send points_to until reviewed
    return jsonify({
        "found": True,
        "clue": {
            "id": clue.id,
            "type": clue.type.value,
            "description": clue.description,
            "strength": clue.strength,
            "location": clue.location,
            "thread": clue.thread,
            "is_dead_end": clue.is_dead_end,
            "reveals_truth": clue.reveals_truth,
            # points_to hidden until reviewed
        },
    })


@app.route('/api/interview', methods=['POST'])
def interview():
    """Interview a suspect."""
    if not current_case or not game_state["started"]:
        return jsonify({"error": "No active case"}), 400

    data = request.json or {}
    suspect_name = data.get("suspect", "")

    suspect = None
    for s in current_case.suspects:
        if s.name == suspect_name:
            suspect = s
            break

    if not suspect:
        return jsonify({"error": f"Unknown suspect: {suspect_name}"}), 404

    is_killer = suspect == current_case.killer
    found_ids = set(game_state["found_clues"])

    if suspect_name in game_state["interviewed"]:
        # Already interviewed — return follow-ups with unlock status
        follow_ups = []
        if suspect.dialogue:
            for fu in suspect.dialogue.follow_ups:
                unlocked = fu.requires_clue is None or fu.requires_clue in found_ids
                follow_ups.append({
                    "topic": fu.topic,
                    "response": fu.response if unlocked else None,
                    "unlocked": unlocked,
                    "requires_clue": fu.requires_clue if not unlocked else None,
                })
        return jsonify({
            "suspect": suspect_name,
            "already_interviewed": True,
            "follow_ups": follow_ups,
        })

    game_state["interviewed"].append(suspect_name)
    game_state["turn"] += 1

    # Return initial statement + follow-up topics (not responses yet)
    follow_ups = []
    if suspect.dialogue:
        for fu in suspect.dialogue.follow_ups:
            unlocked = fu.requires_clue is None or fu.requires_clue in found_ids
            follow_ups.append({
                "topic": fu.topic,
                "unlocked": unlocked,
                "requires_clue": fu.requires_clue if not unlocked else None,
            })

    response = {
        "suspect": suspect_name,
        "personality": suspect.personality,
        "alibi": suspect.alibi_claim,
        "relationship": suspect.relationship_to_victim,
        "demeanor": _get_demeanor(suspect, is_killer),
        "initial_statement": suspect.dialogue.initial_statement if suspect.dialogue else "",
        "follow_ups": follow_ups,
    }

    return jsonify(response)


@app.route('/api/followup', methods=['POST'])
def followup():
    """Get response to a specific follow-up topic."""
    if not current_case or not game_state["started"]:
        return jsonify({"error": "No active case"}), 400

    data = request.json or {}
    suspect_name = data.get("suspect", "")
    topic = data.get("topic", "")

    suspect = None
    for s in current_case.suspects:
        if s.name == suspect_name:
            suspect = s
            break

    if not suspect or not suspect.dialogue:
        return jsonify({"error": "Unknown suspect"}), 404

    found_ids = set(game_state["found_clues"])

    for fu in suspect.dialogue.follow_ups:
        if fu.topic == topic:
            unlocked = fu.requires_clue is None or fu.requires_clue in found_ids
            if not unlocked:
                return jsonify({"error": "Locked", "requires_clue": fu.requires_clue}), 403
            return jsonify({
                "topic": fu.topic,
                "response": fu.response,
            })

    return jsonify({"error": "Topic not found"}), 404


@app.route('/api/locations')
def get_locations():
    """List searchable locations."""
    if not current_case:
        return jsonify({"locations": []})

    locs = set()
    locs.add(current_case.crime_scene)
    for clue in current_case.clues:
        locs.add(clue.location)
    for s in current_case.suspects:
        locs.add(f"interview with {s.name}")

    return jsonify({"locations": sorted(locs)})


@app.route('/api/clues')
def get_found_clues():
    """Return all found clues (points_to hidden unless reviewed)."""
    if not current_case:
        return jsonify({"clues": []})

    reviewed = set(game_state["reviewed_clues"])
    found = []
    for cid in game_state["found_clues"]:
        for clue in current_case.clues:
            if clue.id == cid:
                clue_data = {
                    "id": clue.id,
                    "type": clue.type.value,
                    "description": clue.description,
                    "strength": clue.strength,
                    "thread": clue.thread,
                    "is_dead_end": clue.is_dead_end,
                    "reveals_truth": clue.reveals_truth,
                    "reviewed": clue.id in reviewed,
                }
                if clue.id in reviewed:
                    clue_data["points_to"] = clue.points_to
                found.append(clue_data)

    return jsonify({
        "clues": found,
        "total_found": len(found),
        "total_available": len(current_case.clues),
    })


@app.route('/api/review/<clue_id>', methods=['POST'])
def review_clue(clue_id):
    """Mark a clue as reviewed — reveals points_to analysis."""
    if not current_case or not game_state["started"]:
        return jsonify({"error": "No active case"}), 400

    if clue_id not in game_state["found_clues"]:
        return jsonify({"error": "Clue not found yet"}), 404

    if clue_id in game_state["reviewed_clues"]:
        return jsonify({"message": "Already reviewed"})

    game_state["reviewed_clues"].append(clue_id)

    # Return the full analysis
    for clue in current_case.clues:
        if clue.id == clue_id:
            return jsonify({
                "id": clue.id,
                "points_to": clue.points_to,
                "strength": clue.strength,
                "thread": clue.thread,
                "is_dead_end": clue.is_dead_end,
                "reveals_truth": clue.reveals_truth,
            })

    return jsonify({"error": "Clue not in case"}), 404


@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get all player notes."""
    return jsonify({"notes": game_state.get("notes", [])})


@app.route('/api/notes', methods=['POST'])
def add_note():
    """Add a player note."""
    if not game_state["started"]:
        return jsonify({"error": "No active case"}), 400

    data = request.json or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Note text required"}), 400

    note = {
        "id": f"note_{len(game_state['notes'])}_{int(time.time())}",
        "text": text,
        "tagged_suspect": data.get("suspect"),
        "tagged_evidence": data.get("evidence_id"),
        "timestamp": int(time.time()),
    }
    game_state["notes"].append(note)
    return jsonify(note)


@app.route('/api/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a player note."""
    game_state["notes"] = [n for n in game_state["notes"] if n["id"] != note_id]
    return jsonify({"deleted": True})


@app.route('/api/accuse', methods=['POST'])
def accuse():
    """Make a final accusation."""
    if not current_case or not game_state["started"]:
        return jsonify({"error": "No active case"}), 400

    data = request.json or {}
    accused = data.get("suspect", "")

    correct = accused == current_case.killer.name
    game_state["accusation"] = accused

    response = {
        "correct": correct,
        "accused": accused,
        "killer": current_case.killer.name,
    }

    if correct:
        response["truth"] = current_case.truth
        response["solution"] = current_case.solution_summary
    else:
        response["hint"] = "That's not right. Review your evidence more carefully."

    return jsonify(response)


@app.route('/api/state')
def get_state():
    """Get current game state."""
    if not current_case:
        return jsonify({"started": False})

    return jsonify({
        "started": game_state["started"],
        "turn": game_state["turn"],
        "found_clues": len(game_state["found_clues"]),
        "reviewed_clues": len(game_state["reviewed_clues"]),
        "total_clues": len(current_case.clues),
        "interviewed": len(game_state["interviewed"]),
        "total_suspects": len(current_case.suspects),
        "accusation": game_state["accusation"],
        "notes": len(game_state["notes"]),
    })


def _get_demeanor(suspect, is_killer):
    if is_killer:
        return random.choice(["guarded", "cooperative but tense", "overly calm", "fidgety"])
    else:
        return random.choice(["cooperative", "nervous", "forthcoming", "reluctant"])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
