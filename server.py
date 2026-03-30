#!/usr/bin/env python3
"""
Cold Truth — Game Shell
Serves the detective game UI and API.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from case_generator import generate_case, TestCase, EvidenceType
import os

app = Flask(__name__, static_folder='.')
CORS(app)

# In-memory game state
current_case: TestCase | None = None
game_state = {
    "started": False,
    "found_clues": [],
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
        "interviewed": [],
        "notes": [],
        "accusation": None,
        "turn": 0,
    }
    return jsonify({
        "victim": {
            "name": current_case.victim.name,
            "role": "victim",
        },
        "suspects": [
            {
                "name": s.name,
                "role": s.role,
                "personality": s.personality,
                "relationship": s.relationship_to_victim,
            }
            for s in current_case.suspects
        ],
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
    
    # Find unfound clues at this location
    found_ids = set(game_state["found_clues"])
    available = []
    
    for clue in current_case.clues:
        if clue.id in found_ids:
            continue
        if clue.location.lower() != location:
            continue
        # Check prerequisites
        if any(req not in found_ids for req in clue.requires):
            continue
        available.append(clue)
    
    if not available:
        # Check if there ARE clues here but locked behind prerequisites
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
    
    # Find the most relevant available clue
    clue = available[0]
    game_state["found_clues"].append(clue.id)
    game_state["turn"] += 1
    
    return jsonify({
        "found": True,
        "clue": {
            "id": clue.id,
            "type": clue.type.value,
            "description": clue.description,
            "strength": clue.strength,
            "location": clue.location,
            "points_to": clue.points_to,
            "reveals_truth": clue.reveals_truth,
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
    
    if suspect_name in game_state["interviewed"]:
        # Already interviewed — ask deeper questions based on found clues
        return jsonify({
            "suspect": suspect_name,
            "already_interviewed": True,
            "deeper_questions": _get_deeper_questions(suspect),
        })
    
    game_state["interviewed"].append(suspect_name)
    game_state["turn"] += 1
    
    is_killer = suspect == current_case.killer
    
    response = {
        "suspect": suspect_name,
        "personality": suspect.personality,
        "alibi": suspect.alibi_claim,
        "relationship": suspect.relationship_to_victim,
        "demeanor": _get_demeanor(suspect, is_killer),
        "initial_statement": _get_statement(suspect, is_killer),
    }
    
    return jsonify(response)


@app.route('/api/locations')
def get_locations():
    """List searchable locations."""
    if not current_case:
        return jsonify({"locations": []})
    
    locs = set()
    locs.add(current_case.crime_scene)
    for clue in current_case.clues:
        locs.add(clue.location)
    # Also add interview locations
    for s in current_case.suspects:
        locs.add(f"interview with {s.name}")
    
    return jsonify({"locations": sorted(locs)})


@app.route('/api/clues')
def get_found_clues():
    """Return all found clues."""
    if not current_case:
        return jsonify({"clues": []})
    
    found = []
    for cid in game_state["found_clues"]:
        for clue in current_case.clues:
            if clue.id == cid:
                found.append({
                    "id": clue.id,
                    "type": clue.type.value,
                    "description": clue.description,
                    "strength": clue.strength,
                    "points_to": clue.points_to,
                    "reveals_truth": clue.reveals_truth,
                })
    
    return jsonify({
        "clues": found,
        "total_found": len(found),
        "total_available": len(current_case.clues),
    })


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
        "total_clues": len(current_case.clues),
        "interviewed": len(game_state["interviewed"]),
        "total_suspects": len(current_case.suspects),
        "accusation": game_state["accusation"],
    })


# ── Helper functions ──────────────────────────────────────────────────

def _get_demeanor(suspect, is_killer):
    if is_killer:
        return random.choice(["guarded", "cooperative but tense", "overly calm", "fidgety"])
    else:
        return random.choice(["cooperative", "nervous", "forthcoming", "reluctant"])


def _get_statement(suspect, is_killer):
    if is_killer:
        return (
            f"I was {suspect.alibi_claim}. I know nothing about what happened "
            f"to the victim. This is a terrible tragedy."
        )
    else:
        return (
            f"I was {suspect.alibi_claim}. I can't believe this happened. "
            f"The victim and I... well, we had our differences, but I would never..."
        )


def _get_deeper_questions(suspect):
    """Generate follow-up questions based on found clues."""
    questions = []
    found_ids = set(game_state["found_clues"])
    
    for clue in current_case.clues:
        if clue.id not in found_ids:
            continue
        if suspect.name in clue.description:
            questions.append({
                "topic": f"About the evidence: {clue.description[:50]}...",
                "response": _get_evidence_response(suspect, clue),
            })
    
    if not questions:
        questions.append({
            "topic": "General follow-up",
            "response": f"I've already told you everything I know. I was {suspect.alibi_claim}.",
        })
    
    return questions


def _get_evidence_response(suspect, clue):
    is_killer = suspect == current_case.killer
    if clue.points_to == suspect.name and is_killer:
        return "That's... taken out of context. You're twisting the facts."
    elif clue.points_to == suspect.name:
        return "I can explain that. It's not what it looks like."
    else:
        return "I don't know anything about that."


import random

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
