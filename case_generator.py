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
    PHYSICAL = "physical"      # Objects found at scene
    TESTIMONY = "testimony"    # What someone says
    DOCUMENT = "document"      # Papers, records
    FORENSIC = "forensic"      # Lab results, analysis
    CIRCUMSTANTIAL = "circumstantial"  # Behavior, timing


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
    "business partner",
    "personal secretary",
    "estranged spouse",
    "rival",
    "old friend",
    "employee",
    "neighbor",
    "physician",
    "lawyer",
    "housekeeper",
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
class Person:
    name: str
    role: str
    personality: str  # one-word trait
    alibi_claim: str  # what they claim they were doing
    secret: str       # something they're hiding (not necessarily murder-related)
    relationship_to_victim: str


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
    points_to: str          # who this implicates (or "nobody" for red herring)
    strength: int           # 1-5, how directly it points
    requires: list[str]     # clue IDs that must be found first
    reveals_truth: bool     # does this directly confirm the killer?
    mentions_locations: list[str] = field(default_factory=list)  # locations mentioned in description


@dataclass
class TestCase:
    """A fully generated murder case."""
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
    truth: str  # plain-English explanation of what actually happened
    solution_summary: str


def generate_case(seed: Optional[int] = None) -> TestCase:
    """Generate a complete, consistent murder case."""
    rng = random.Random(seed)
    
    # ── 1. Create the victim ──────────────────────────────────────────
    victim_last = rng.choice(LAST_NAMES)
    victim_first = rng.choice(FIRST_NAMES_M + FIRST_NAMES_F)
    victim = Person(
        name=f"{victim_first} {victim_last}",
        role="victim",
        personality="wealthy",
        alibi_claim="",
        secret="",
        relationship_to_victim="self"
    )
    
    # ── 2. Create suspects ────────────────────────────────────────────
    num_suspects = rng.randint(4, 6)
    used_first = {victim_first}
    used_last = {victim_last}
    suspects = []
    
    for i in range(num_suspects):
        # One suspect shares the last name (family/spouse)
        if i == 0:
            first = rng.choice([n for n in (FIRST_NAMES_F + FIRST_NAMES_M) if n not in used_first])
            last = victim_last  # same family
        else:
            first = rng.choice([n for n in (FIRST_NAMES_F + FIRST_NAMES_M) if n not in used_first])
            last = rng.choice([n for n in LAST_NAMES if n not in used_last])
        
        used_first.add(first)
        used_last.add(last)
        
        personality = rng.choice([
            "nervous", "arrogant", "quiet", "charming", "cold",
            "warm", "evasive", "honest", "bitter", "loyal"
        ])
        
        role = rng.choice(ROLES)
        
        # Generate alibi claim
        alibi_location = rng.choice(LOCATIONS)
        alibi_action = rng.choice([
            "reading", "resting", "working", "talking on the phone",
            "having tea", "taking a walk", "attending to correspondence"
        ])
        
        # Generate a personal secret (embarrassing but not murderous)
        secret = rng.choice([
            f"has gambling debts",
            f"was having an affair",
            f"was being blackmailed",
            f"stole money from the household accounts",
            f"lied about {rng.choice(['their alibi', 'where they were', 'who they spoke to'])}",
            f"was planning to leave town",
            f"discovered the victim's will had been changed",
        ])
        
        suspects.append(Person(
            name=f"{first} {last}",
            role=role,
            personality=personality,
            alibi_claim=f"was {alibi_action} in {alibi_location}",
            secret=secret,
            relationship_to_victim=role,
        ))
    
    # ── 3. Choose the killer and truth ────────────────────────────────
    killer = rng.choice(suspects)
    cause = rng.choice(list(CauseOfDeath))
    motive = rng.choice(list(Motive))
    weapon = rng.choice(WEAPON_OBJECTS[cause])
    crime_scene = rng.choice(LOCATIONS)
    
    # Time of death: pick a slot
    tod_slots = list(TimeSlot)
    time_of_death = rng.choice(tod_slots[4:])  # afternoon or later
    tod_idx = tod_slots.index(time_of_death)
    
    # ── 4. Build timeline ─────────────────────────────────────────────
    timeline = []
    
    # Killer's movements (truth)
    # Before murder: seen somewhere else
    pre_loc = rng.choice([l for l in LOCATIONS if l != crime_scene])
    timeline.append(TimelineEntry(
        time=tod_slots[max(0, tod_idx - 2)],
        person=killer.name,
        action=f"was seen in {pre_loc}",
        location=pre_loc,
        witnessed_by=[rng.choice([s.name for s in suspects if s != killer])],
    ))
    
    # Time of death: killer at crime scene
    timeline.append(TimelineEntry(
        time=time_of_death,
        person=killer.name,
        action=f"committed murder in {crime_scene} using {weapon}",
        location=crime_scene,
        witnessed_by=[],  # Nobody saw this — the killer made sure
    ))
    
    # After murder: killer appears elsewhere
    post_loc = rng.choice([l for l in LOCATIONS if l != crime_scene])
    timeline.append(TimelineEntry(
        time=tod_slots[min(len(tod_slots) - 1, tod_idx + 1)],
        person=killer.name,
        action=f"appeared in {post_loc}, looking flustered",
        location=post_loc,
        witnessed_by=[rng.choice([s.name for s in suspects if s != killer])],
    ))
    
    # Other suspects' movements
    for s in suspects:
        if s == killer:
            continue
        # Where they actually were (truth)
        s_loc = rng.choice(LOCATIONS)
        s_action = rng.choice([
            "was having a quiet drink",
            "was arguing with someone on the phone",
            "was packing a suitcase",
            "was writing a letter",
            "was staring out the window",
            "was tending to the fire",
            "was resting",
        ])
        other_names = [s2.name for s2 in suspects if s2 != s and s2 != killer]
        witnessed = rng.choice(other_names) if other_names else ""
        timeline.append(TimelineEntry(
            time=time_of_death,
            person=s.name,
            action=s_action,
            location=s_loc,
            witnessed_by=[witnessed] if rng.random() > 0.3 else [],
        ))
    
    # ── 5. Generate clues ─────────────────────────────────────────────
    clues = []
    clue_id = 0
    
    def make_clue(etype, desc, loc, points_to, strength, requires=None, reveals=False):
        nonlocal clue_id
        cid = f"clue_{clue_id}"
        clue_id += 1
        return Clue(
            id=cid, type=etype, description=desc, location=loc,
            points_to=points_to, strength=strength,
            requires=requires or [], reveals_truth=reveals,
        )
    
    # SCENE CLUES (always findable at crime scene)
    clues.append(make_clue(
        EvidenceType.FORENSIC,
        f"The cause of death was {cause.value}.",
        crime_scene, "nobody", 1,
    ))
    
    if cause == CauseOfDeath.STABBING:
        clues.append(make_clue(
            EvidenceType.PHYSICAL,
            f"A bloodied {weapon} was found near the body.",
            crime_scene, killer.name, 2,
        ))
    elif cause == CauseOfDeath.POISON:
        clues.append(make_clue(
            EvidenceType.PHYSICAL,
            f"A glass with residue of {weapon} was found at the scene.",
            crime_scene, killer.name, 2,
        ))
    elif cause == CauseOfDeath.BLUNT_FORCE:
        clues.append(make_clue(
            EvidenceType.PHYSICAL,
            f"{weapon.capitalize()} was found near the body, stained with blood.",
            crime_scene, killer.name, 2,
        ))
    elif cause == CauseOfDeath.STRANGULATION:
        clues.append(make_clue(
            EvidenceType.PHYSICAL,
            f"{weapon.capitalize()} was found nearby, consistent with the marks.",
            crime_scene, killer.name, 2,
        ))
    elif cause == CauseOfDeath.SHOT:
        clues.append(make_clue(
            EvidenceType.PHYSICAL,
            f"{weapon.capitalize()} was found discarded in the bushes outside.",
            crime_scene, killer.name, 2,
        ))
    else:
        clues.append(make_clue(
            EvidenceType.PHYSICAL,
            f"Signs of struggle consistent with {cause.value} were evident.",
            crime_scene, killer.name, 2,
        ))
    
    # ALIBI CONTRADICTION CLUE
    # The killer's claimed alibi doesn't match witness testimony
    witness = rng.choice([s for s in suspects if s != killer])
    clues.append(make_clue(
        EvidenceType.TESTIMONY,
        f"{witness.name} says they did NOT see {killer.name} where {killer.name} claims to have been.",
        f"interview with {witness.name}", killer.name, 3,
        requires=[clues[1].id],  # after finding weapon
    ))
    
    # MOTIVE CLUE
    motive_hints = {
        Motive.JEALOUSY: f"A photograph of the victim with someone {killer.name} cared about was found torn in half.",
        Motive.MONEY: f"Financial records show {killer.name} recently took out a large insurance policy on the victim.",
        Motive.REVENGE: f"A letter from {killer.name} to a friend mentions an old grudge against the victim.",
        Motive.SECRECY: f"The victim's diary mentions discovering something about {killer.name} that 'would ruin them.'",
        Motive.SELF_DEFENSE: f"Medical records show {killer.name} had recent injuries consistent with an altercation.",
        Motive.AMBITION: f"A memo outlines a merger that would have cut {killer.name} out entirely.",
    }
    clues.append(make_clue(
        EvidenceType.DOCUMENT,
        motive_hints[motive],
        rng.choice(LOCATIONS), killer.name, 4,
        requires=[clues[1].id],
    ))
    
    # OPPORTUNITY CLUE (ties killer to scene at time of death)
    # Something physical places them there
    opportunity_clues = [
        f"A {rng.choice(['button', 'glove', 'scarf fragment', 'cufflink'])} matching {killer.name}'s clothing was found in {crime_scene}.",
        f"Footprints matching {killer.name}'s shoes were found near {crime_scene}.",
        f"{killer.name}'s fingerprints were found on the door to {crime_scene}, despite claiming never to have been there.",
    ]
    clues.append(make_clue(
        EvidenceType.FORENSIC,
        rng.choice(opportunity_clues),
        crime_scene, killer.name, 4,
        requires=[clues[2].id],  # after alibi contradiction
    ))
    
    # SMOKING GUN (final confirmation)
    smoking_guns = [
        f"A handwritten confession draft was found in {killer.name}'s room — they started writing it but stopped.",
        f"{killer.name} was overheard arguing with the victim about {motive.value} shortly before the murder.",
        f"Traces of the victim's blood were found on {killer.name}'s clothing.",
        f"A witness saw {killer.name} leaving {crime_scene} around {time_of_death.value}.",
    ]
    clues.append(make_clue(
        EvidenceType.TESTIMONY,
        rng.choice(smoking_guns),
        rng.choice(LOCATIONS), killer.name, 5,
        requires=[clues[3].id, clues[4].id],  # after motive + opportunity
        reveals=True,
    ))
    
    # RED HERRINGS (1-2 clues that point to innocent suspects)
    for _ in range(rng.randint(1, 2)):
        innocent = rng.choice([s for s in suspects if s != killer])
        herring = rng.choice([
            f"{innocent.name} was seen near {crime_scene} earlier that day, but at a different time.",
            f"{innocent.name} had a heated argument with the victim last week.",
            f"A receipt shows {innocent.name} purchased something suspicious recently, but it was a gift.",
            f"{innocent.name}'s fingerprints were on an object at the scene — they'd touched it days before.",
        ])
        clues.append(make_clue(
            EvidenceType.CIRCUMSTANTIAL,
            herring,
            rng.choice(LOCATIONS), innocent.name, rng.randint(1, 2),
            requires=[clues[0].id],
        ))
    
    # ── 6. Build truth narrative ──────────────────────────────────────
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
        f"KEY EVIDENCE: {clues[4].description}"
    )
    
    return TestCase(
        case_id=f"case_{seed or rng.randint(1000,9999)}",
        victim=victim,
        killer=killer,
        suspects=suspects,
        cause_of_death=cause,
        motive=motive,
        weapon=weapon,
        crime_scene=crime_scene,
        time_of_death=time_of_death,
        timeline=timeline,
        clues=clues,
        truth=truth,
        solution_summary=solution_summary,
    )


if __name__ == "__main__":
    # Test generation
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
    print(f"\nClues ({len(case.clues)}):")
    for c in sorted(case.clues, key=lambda c: c.strength):
        print(f"  [{c.strength}] {c.type.value}: {c.description}")
        if c.requires:
            print(f"    Requires: {c.requires}")
    print(f"\nTRUTH: {case.truth}")
