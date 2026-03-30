#!/usr/bin/env python3
"""
Cold Truth — Procedural Detective Game
Case Generator: Creates consistent murder mysteries.

Design principle: Generate TRUTH first, then scatter evidence.
Every clue must be logically derivable from the ground truth.
"""

import random
import json
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CauseOfDeath(Enum):
    BLUNT_FORCE = "blunt force trauma"
    STABBING = "stabbing"
    POISON = "poisoning"
    STRANGULATION = "strangulation"
    SHOT = "gunshot"
    DROWNING = "drowning"


class Motive(Enum):
    JEALOUSY = "jealousy"
    MONEY = "financial gain"
    REVENGE = "revenge"
    SECRECY = "protecting a secret"
    SELF_DEFENSE = "self-defense (claim)"
    AMBITION = "career advancement"


class EvidenceType(Enum):
    PHYSICAL = "physical"
    TESTIMONY = "testimony"
    DOCUMENT = "document"
    FORENSIC = "forensic"
    CIRCUMSTANTIAL = "circumstantial"


class TimeSlot(Enum):
    EARLY_MORNING = "6:00 AM"
    MORNING = "9:00 AM"
    LATE_MORNING = "11:00 AM"
    NOON = "12:00 PM"
    AFTERNOON = "2:00 PM"
    LATE_AFTERNOON = "4:00 PM"
    EVENING = "6:00 PM"
    NIGHT = "9:00 PM"
    LATE_NIGHT = "11:00 PM"
    MIDNIGHT = "12:00 AM"


# ── Archetypes and Names ──────────────────────────────────────────────

FIRST_NAMES_F = ["Eleanor", "Margaret", "Dorothy", "Helen", "Virginia",
                 "Ruth", "Clara", "Irene", "Florence", "Marion",
                 "Vivian", "Sylvia", "Beatrice", "Edith", "Lillian"]
FIRST_NAMES_M = ["Arthur", "Walter", "Harold", "Frederick", "Raymond",
                 "Edgar", "Chester", "Clarence", "Lester", "Milton",
                 "Howard", "Calvin", "Norman", "Everett", "Leland"]
LAST_NAMES = ["Ashworth", "Blackwood", "Chamberlain", "Davenport",
              "Fairfax", "Gallagher", "Hartwell", "Kingsley",
              "Lockwood", "Merritt", "Prescott", "Sinclair",
              "Thornwood", "Underhill", "Whitmore"]

ROLES = [
    "business partner", "personal secretary", "estranged spouse",
    "rival", "old friend", "employee", "neighbor", "physician",
    "lawyer", "housekeeper",
]

LOCATIONS = [
    "the study", "the library", "the garden", "the kitchen",
    "the wine cellar", "the conservatory", "the garage", "the hallway",
    "the dining room", "the bedroom",
]

WEAPON_OBJECTS = {
    CauseOfDeath.BLUNT_FORCE: ["a bronze candlestick", "a fireplace poker", "a heavy statuette"],
    CauseOfDeath.STABBING: ["a letter opener", "a kitchen knife", "a pair of scissors"],
    CauseOfDeath.POISON: ["cyanide", "arsenic", "a lethal dose of medication"],
    CauseOfDeath.STRANGULATION: ["a silk scarf", "a rope", "bare hands"],
    CauseOfDeath.SHOT: ["a .38 revolver", "a hunting rifle", "a pistol"],
    CauseOfDeath.DROWNING: ["the garden pond", "the bathtub", "the fountain"],
}


@dataclass
class FollowUp:
    topic: str
    response: str
    requires_clue: Optional[str] = None  # clue ID needed to unlock


@dataclass
class Dialogue:
    initial_statement: str
    follow_ups: list[FollowUp] = field(default_factory=list)


@dataclass
class Person:
    name: str
    role: str
    personality: str
    alibi_claim: str
    secret: str
    relationship_to_victim: str
    dialogue: Optional[Dialogue] = None


@dataclass
class TimelineEntry:
    time: TimeSlot
    person: str
    action: str
    location: str
    witnessed_by: list[str] = field(default_factory=list)


@dataclass
class Clue:
    id: str
    type: EvidenceType
    description: str
    location: str
    points_to: str
    strength: int
    requires: list[str]
    reveals_truth: bool
    thread: str = ""  # "motive", "opportunity", "means", "convergence", "red_herring"
    is_dead_end: bool = False


@dataclass
class TestCase:
    case_id: str
    victim: Person
    killer: Person
    suspects: list[Person]
    cause_of_death: CauseOfDeath
    motive: Motive
    weapon: str
    crime_scene: str
    time_of_death: TimeSlot
    timeline: list[TimelineEntry]
    clues: list[Clue]
    truth: str
    solution_summary: str


def _build_dialogue(person, is_killer, case_data, rng):
    """Build personality-driven dialogue with branching follow-ups."""
    killer_name = case_data["killer"].name
    victim_name = case_data["victim"].name
    motive_val = case_data["motive"].value
    cause_val = case_data["cause"].value
    weapon = case_data["weapon"]
    crime_scene = case_data["crime_scene"]
    tod = case_data["time_of_death"].value

    if is_killer:
        # Killer's initial statement — tries to sound innocent but has subtle tells
        personality = person.personality
        if personality == "nervous":
            initial = (
                f"I... I was {person.alibi_claim}. I heard about what happened and I just — "
                f"I can't believe it. I hardly ever went near {crime_scene}. "
                f"I barely knew what was going on with {victim_name} lately."
            )
        elif personality == "arrogant":
            initial = (
                f"I was {person.alibi_claim}, as I've already told everyone. "
                f"I had no reason to be anywhere near {crime_scene}. "
                f"Frankly, I was one of the few people who actually respected {victim_name}."
            )
        elif personality == "charming":
            initial = (
                f"Oh, it's just awful, isn't it? I was {person.alibi_claim} at the time. "
                f"I want to help however I can. {victim_name} was... well, we had our moments, "
                f"but nobody deserved this."
            )
        else:
            initial = (
                f"I was {person.alibi_claim}. I know nothing about what happened "
                f"to {victim_name}. This is a terrible tragedy. I was nowhere near {crime_scene}."
            )

        # Killer follow-ups — some subtly contradict evidence
        follow_ups = [
            FollowUp(
                topic="their alibi",
                response=f"I already told you — I was {person.alibi_claim}. "
                         f"I didn't leave there until well after {tod}. "
                         f"Nobody can confirm that? Well, I was alone. That's not a crime.",
                requires_clue=None,
            ),
            FollowUp(
                topic="the victim",
                response=f"{victim_name} and I had a perfectly fine relationship. "
                         f"Nothing unusual. People like to gossip, but we were on good terms. "
                         f"I barely even saw them that day.",
                requires_clue=None,
            ),
            FollowUp(
                topic="other suspects",
                response=f"I saw a few people around that evening, but I wasn't paying close attention. "
                         f"I try to mind my own business.",
                requires_clue=None,
            ),
            FollowUp(
                topic="their secret",
                response=f"I don't know what you're implying. Everyone has private matters. "
                         f"That has nothing to do with what happened to {victim_name}. "
                         f"You're grasping at straws.",
                requires_clue=None,  # unlocked by motive thread clue
            ),
        ]
    else:
        # Innocent suspect — has useful info if you ask right questions
        personality = person.personality
        if personality == "honest":
            initial = (
                f"I was {person.alibi_claim}. I still can't believe this happened. "
                f"I want to help — I'll tell you anything you need to know."
            )
        elif personality == "nervous":
            initial = (
                f"I was {person.alibi_claim}. I — look, I barely slept, "
                f"I've been worried sick. What if the killer comes after me too?"
            )
        elif personality == "cold":
            initial = (
                f"I was {person.alibi_claim}. I won't pretend I liked {victim_name}, "
                f"but I had nothing to do with this. Ask me what you need to ask."
            )
        elif personality == "bitter":
            initial = (
                f"I was {person.alibi_claim}. And before you ask — yes, "
                f"{victim_name} and I had our problems. Doesn't mean I killed them."
            )
        else:
            initial = (
                f"I was {person.alibi_claim}. I can't believe this happened. "
                f"The victim and I... well, we had our differences, but I would never..."
            )

        follow_ups = [
            FollowUp(
                topic="their alibi",
                response=f"I was definitely {person.alibi_claim}. "
                         f"Ask around — someone should be able to confirm at least part of that.",
                requires_clue=None,
            ),
            FollowUp(
                topic="the victim",
                response=f"{victim_name} was... complicated. Had a lot of people in their life, "
                         f"and not all of them friendly. I know {killer_name} had been "
                         f"acting strange around them lately.",
                requires_clue=None,
            ),
            FollowUp(
                topic="other suspects",
                response=f"I've noticed {killer_name} has been on edge lately. "
                         f"Can't say more than that, but you might want to look into them.",
                requires_clue=None,
            ),
            FollowUp(
                topic="their secret",
                response=f"I'd rather not talk about that. It's personal and it has nothing "
                         f"to do with the murder. I swear.",
                requires_clue=None,
            ),
        ]

    return Dialogue(initial_statement=initial, follow_ups=follow_ups)


def _set_requires_clue_for_secrets(suspects, clues, rng):
    """Set requires_clue on 'their secret' follow-ups to reference motive-thread clues."""
    motive_clues = [c for c in clues if c.thread == "motive"]
    for s in suspects:
        if s.dialogue:
            for fu in s.dialogue.follow_ups:
                if fu.topic == "their secret" and motive_clues:
                    fu.requires_clue = rng.choice(motive_clues).id


def generate_case(seed: Optional[int] = None) -> TestCase:
    rng = random.Random(seed)

    # ── 1. Create the victim ──────────────────────────────────────────
    victim_last = rng.choice(LAST_NAMES)
    victim_first = rng.choice(FIRST_NAMES_M + FIRST_NAMES_F)
    victim = Person(
        name=f"{victim_first} {victim_last}",
        role="victim", personality="wealthy",
        alibi_claim="", secret="", relationship_to_victim="self",
    )

    # ── 2. Create suspects ────────────────────────────────────────────
    num_suspects = rng.randint(4, 6)
    used_first = {victim_first}
    used_last = {victim_last}
    suspects = []

    for i in range(num_suspects):
        if i == 0:
            first = rng.choice([n for n in (FIRST_NAMES_F + FIRST_NAMES_M) if n not in used_first])
            last = victim_last
        else:
            first = rng.choice([n for n in (FIRST_NAMES_F + FIRST_NAMES_M) if n not in used_first])
            last = rng.choice([n for n in LAST_NAMES if n not in used_last])

        used_first.add(first)
        used_last.add(last)

        personality = rng.choice([
            "nervous", "arrogant", "quiet", "charming", "cold",
            "warm", "evasive", "honest", "bitter", "loyal",
        ])
        role = rng.choice(ROLES)
        alibi_location = rng.choice(LOCATIONS)
        alibi_action = rng.choice([
            "reading", "resting", "working", "talking on the phone",
            "having tea", "taking a walk", "attending to correspondence",
        ])
        secret = rng.choice([
            "has gambling debts",
            "was having an affair",
            "was being blackmailed",
            "stole money from the household accounts",
            f"lied about {rng.choice(['their alibi', 'where they were', 'who they spoke to'])}",
            "was planning to leave town",
            "discovered the victim's will had been changed",
        ])

        suspects.append(Person(
            name=f"{first} {last}", role=role, personality=personality,
            alibi_claim=f"was {alibi_action} in {alibi_location}",
            secret=secret, relationship_to_victim=role,
        ))

    # ── 3. Choose the killer and truth ────────────────────────────────
    killer = rng.choice(suspects)
    cause = rng.choice(list(CauseOfDeath))
    motive = rng.choice(list(Motive))
    weapon = rng.choice(WEAPON_OBJECTS[cause])
    crime_scene = rng.choice(LOCATIONS)

    tod_slots = list(TimeSlot)
    time_of_death = rng.choice(tod_slots[4:])
    tod_idx = tod_slots.index(time_of_death)

    # ── 4. Build timeline ─────────────────────────────────────────────
    timeline = []
    pre_loc = rng.choice([l for l in LOCATIONS if l != crime_scene])
    timeline.append(TimelineEntry(
        time=tod_slots[max(0, tod_idx - 2)],
        person=killer.name,
        action=f"was seen in {pre_loc}",
        location=pre_loc,
        witnessed_by=[rng.choice([s.name for s in suspects if s != killer])],
    ))
    timeline.append(TimelineEntry(
        time=time_of_death,
        person=killer.name,
        action=f"committed murder in {crime_scene} using {weapon}",
        location=crime_scene,
        witnessed_by=[],
    ))
    post_loc = rng.choice([l for l in LOCATIONS if l != crime_scene])
    timeline.append(TimelineEntry(
        time=tod_slots[min(len(tod_slots) - 1, tod_idx + 1)],
        person=killer.name,
        action=f"appeared in {post_loc}, looking flustered",
        location=post_loc,
        witnessed_by=[rng.choice([s.name for s in suspects if s != killer])],
    ))

    for s in suspects:
        if s == killer:
            continue
        s_loc = rng.choice(LOCATIONS)
        s_action = rng.choice([
            "was having a quiet drink", "was arguing with someone on the phone",
            "was packing a suitcase", "was writing a letter",
            "was staring out the window", "was tending to the fire", "was resting",
        ])
        other_names = [s2.name for s2 in suspects if s2 != s and s2 != killer]
        witnessed = rng.choice(other_names) if other_names else ""
        timeline.append(TimelineEntry(
            time=time_of_death, person=s.name, action=s_action, location=s_loc,
            witnessed_by=[witnessed] if rng.random() > 0.3 else [],
        ))

    # ── 5. Generate branching clues ───────────────────────────────────
    clues = []
    clue_id = 0

    def make_clue(etype, desc, loc, points_to, strength, requires=None,
                  reveals=False, thread="", is_dead_end=False):
        nonlocal clue_id
        cid = f"clue_{clue_id}"
        clue_id += 1
        return Clue(
            id=cid, type=etype, description=desc, location=loc,
            points_to=points_to, strength=strength,
            requires=requires or [], reveals_truth=reveals,
            thread=thread, is_dead_end=is_dead_end,
        )

    # --- SCENE CLUE (entry point, no prerequisites) ---
    scene_clue = make_clue(
        EvidenceType.FORENSIC,
        f"The cause of death was {cause.value}.",
        crime_scene, "nobody", 1, thread="scene",
    )
    clues.append(scene_clue)

    weapon_descs = {
        CauseOfDeath.STABBING: f"A bloodied {weapon} was found near the body.",
        CauseOfDeath.POISON: f"A glass with residue of {weapon} was found at the scene.",
        CauseOfDeath.BLUNT_FORCE: f"{weapon.capitalize()} was found near the body, stained with blood.",
        CauseOfDeath.STRANGULATION: f"{weapon.capitalize()} was found nearby, consistent with the marks.",
        CauseOfDeath.SHOT: f"{weapon.capitalize()} was found discarded in the bushes outside.",
        CauseOfDeath.DROWNING: f"Signs of struggle consistent with {cause.value} were evident.",
    }
    weapon_clue = make_clue(
        EvidenceType.PHYSICAL,
        weapon_descs.get(cause, f"Signs of {cause.value} were evident."),
        crime_scene, killer.name, 2, thread="scene",
    )
    clues.append(weapon_clue)

    # --- THREAD 1: MOTIVE ---
    motive_hints = {
        Motive.JEALOUSY: f"A photograph of the victim with someone {killer.name} cared about was found torn in half.",
        Motive.MONEY: f"Financial records show {killer.name} recently took out a large insurance policy on the victim.",
        Motive.REVENGE: f"A letter from {killer.name} to a friend mentions an old grudge against the victim.",
        Motive.SECRECY: f"The victim's diary mentions discovering something about {killer.name} that 'would ruin them.'",
        Motive.SELF_DEFENSE: f"Medical records show {killer.name} had recent injuries consistent with an altercation.",
        Motive.AMBITION: f"A memo outlines a merger that would have cut {killer.name} out entirely.",
    }
    motive1 = make_clue(
        EvidenceType.DOCUMENT,
        motive_hints[motive],
        rng.choice([l for l in LOCATIONS if l != crime_scene]),
        killer.name, 3, thread="motive",
    )
    clues.append(motive1)

    # Second motive clue — deeper
    motive2 = make_clue(
        EvidenceType.DOCUMENT,
        f"Among {victim.name}'s papers, a note reads: 'If anything happens to me, look into {killer.name}'s dealings with {motive.value}.'",
        "the study", killer.name, 4,
        requires=[motive1.id], thread="motive",
    )
    clues.append(motive2)

    # --- THREAD 2: OPPORTUNITY ---
    witness = rng.choice([s for s in suspects if s != killer])
    opp1 = make_clue(
        EvidenceType.TESTIMONY,
        f"{witness.name} says they did NOT see {killer.name} where {killer.name} claims to have been.",
        f"interview with {witness.name}", killer.name, 3,
        thread="opportunity",
    )
    clues.append(opp1)

    opportunity_items = [
        f"A {rng.choice(['button', 'glove', 'scarf fragment', 'cufflink'])} matching {killer.name}'s clothing was found in {crime_scene}.",
        f"Footprints matching {killer.name}'s shoes were found near {crime_scene}.",
        f"{killer.name}'s fingerprints were found on the door to {crime_scene}, despite claiming never to have been there.",
    ]
    opp2 = make_clue(
        EvidenceType.FORENSIC,
        rng.choice(opportunity_items),
        crime_scene, killer.name, 4,
        requires=[opp1.id], thread="opportunity",
    )
    clues.append(opp2)

    # --- THREAD 3: MEANS ---
    means1 = make_clue(
        EvidenceType.CIRCUMSTANTIAL,
        f"Records show {killer.name} had access to {weapon} — it was stored in a location only they had the key to.",
        rng.choice(LOCATIONS), killer.name, 3,
        thread="means",
    )
    clues.append(means1)

    means2 = make_clue(
        EvidenceType.PHYSICAL,
        f"Traces consistent with {weapon} were found on {killer.name}'s personal belongings.",
        rng.choice(LOCATIONS), killer.name, 4,
        requires=[means1.id], thread="means",
    )
    clues.append(means2)

    # --- CONVERGENCE: SMOKING GUN (requires 2+ threads) ---
    # Pick one clue from each of two different threads
    smoking_gun = make_clue(
        EvidenceType.TESTIMONY,
        rng.choice([
            f"A witness saw {killer.name} leaving {crime_scene} around {time_of_death.value}, "
            f"looking distressed and carrying something that could have been {weapon}.",
            f"{killer.name} was overheard arguing with the victim about {motive.value} "
            f"shortly before {time_of_death.value}.",
            f"A handwritten note in {killer.name}'s room reads: 'I had no choice. "
            f"They were going to destroy me.' Dated the evening of the murder.",
        ]),
        rng.choice(LOCATIONS), killer.name, 5,
        requires=[motive2.id, opp2.id],  # need motive AND opportunity threads
        reveals=True, thread="convergence",
    )
    clues.append(smoking_gun)

    # --- RED HERRINGS (2-3 dead ends) ---
    for _ in range(rng.randint(2, 3)):
        innocent = rng.choice([s for s in suspects if s != killer])
        herring_desc = rng.choice([
            f"{innocent.name} was seen near {crime_scene} earlier that day, but at a different time.",
            f"{innocent.name} had a heated argument with the victim last week.",
            f"A receipt shows {innocent.name} purchased something suspicious recently, but it was a gift.",
            f"{innocent.name}'s fingerprints were on an object at the scene — they'd touched it days before.",
            f"{innocent.name} was overheard making threats about the victim, but they were just venting.",
        ])
        clues.append(make_clue(
            EvidenceType.CIRCUMSTANTIAL,
            herring_desc,
            rng.choice(LOCATIONS), innocent.name, rng.randint(2, 3),
            requires=[scene_clue.id], thread="red_herring", is_dead_end=True,
        ))

    # ── 6. Build dialogues ────────────────────────────────────────────
    case_data_ref = {
        "killer": killer, "victim": victim,
        "motive": motive, "cause": cause, "weapon": weapon,
        "crime_scene": crime_scene, "time_of_death": time_of_death,
    }
    for s in suspects:
        s.dialogue = _build_dialogue(s, s == killer, case_data_ref, rng)

    # Set requires_clue on secret follow-ups
    _set_requires_clue_for_secrets(suspects, clues, rng)

    # ── 7. Build truth narrative ──────────────────────────────────────
    truth = (
        f"{killer.name} killed {victim.name} by {cause.value} in {crime_scene} "
        f"around {time_of_death.value}. The motive was {motive.value}. "
        f"They used {weapon}. After the murder, they went to {post_loc} "
        f"and tried to establish an alibi, claiming they were "
        f"{killer.alibi_claim}. However, {witness.name} contradicts this."
    )

    solution_summary = (
        f"KILLER: {killer.name}\n"
        f"CAUSE: {cause.value}\n"
        f"WEAPON: {weapon}\n"
        f"SCENE: {crime_scene}\n"
        f"TIME: {time_of_death.value}\n"
        f"MOTIVE: {motive.value}\n"
        f"KEY EVIDENCE: {smoking_gun.description}"
    )

    return TestCase(
        case_id=f"case_{seed or rng.randint(1000,9999)}",
        victim=victim, killer=killer, suspects=suspects,
        cause_of_death=cause, motive=motive, weapon=weapon,
        crime_scene=crime_scene, time_of_death=time_of_death,
        timeline=timeline, clues=clues, truth=truth,
        solution_summary=solution_summary,
    )


if __name__ == "__main__":
    case = generate_case(seed=42)
    print(f"=== {case.victim.name} was murdered ===")
    print(f"Scene: {case.crime_scene}")
    print(f"Cause: {case.cause_of_death.value}")
    print(f"Weapon: {case.weapon}")
    print(f"Time: {case.time_of_death.value}")
    print(f"\nSuspects:")
    for s in case.suspects:
        print(f"  {s.name} ({s.role}, {s.personality})")
        print(f"    Alibi: {s.alibi_claim}")
        print(f"    Secret: {s.secret}")
        if s.dialogue:
            print(f"    Initial: {s.dialogue.initial_statement}")
            for fu in s.dialogue.follow_ups:
                lock = f" [requires {fu.requires_clue}]" if fu.requires_clue else ""
                print(f"    Follow-up '{fu.topic}'{lock}: {fu.response[:60]}...")
    print(f"\nClues ({len(case.clues)}):")
    for c in case.clues:
        dead = " [DEAD END]" if c.is_dead_end else ""
        print(f"  [{c.thread}] [{c.strength}] {c.type.value}: {c.description}")
        if c.requires:
            print(f"    Requires: {c.requires}")
    print(f"\nTRUTH: {case.truth}")
