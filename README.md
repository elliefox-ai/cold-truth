# Cold Truth 🔍

A procedural detective game where every case is logically solvable. No guessing, no luck — pure deduction.

## How It Works

The case generator builds **truth first, then scatters evidence**. Every clue is logically derivable from the ground truth, so a careful player can always solve the case through investigation alone.

### Case Generation

Each playthrough generates a unique murder mystery:

- **Victim & suspects** — 4-6 suspects with distinct personalities, roles, alibis, and secrets
- **Branching dialogue** — Each suspect has personality-driven responses with follow-up topics that unlock based on evidence you've found
- **Clue dependency graph** — Clues are organized into three investigative threads:
  - **Motive** — Why did they do it?
  - **Opportunity** — Could they have done it?
  - **Means** — How did they do it?
- **Convergence evidence** — The smoking gun only becomes available after you've followed two threads deep enough
- **Red herrings** — 2-3 dead-end clues per case designed to mislead. A good detective has to separate signal from noise

### Gameplay

1. **Investigate locations** — Search rooms to find clues. Some clues are locked until you've found prerequisite evidence.
2. **Interview suspects** — Talk to suspects to get alibis, relationships, and behavioral tells. Follow-up questions unlock as you gather evidence.
3. **Review evidence** — Found clues reveal more detail when reviewed (who they point to, how strong they are).
4. **Make an accusation** — When you're confident, accuse a suspect. Get it right and you see the full truth. Get it wrong and you get a hint to keep investigating.

### Evidence System

Clues have **strength ratings** (1-5) indicating how strongly they point toward a suspect. But strength alone doesn't solve the case — you need to build a complete picture across all three threads (motive + opportunity + means) before the convergence evidence becomes available.

## Running

```bash
pip install flask flask-cors
python server.py
```

Then open `http://localhost:5001` in your browser.

## Tech

- **Backend**: Python + Flask
- **Frontail**: Single-page HTML/JS
- **Case generator**: Pure Python dataclass-based procedural generation

## License

MIT
