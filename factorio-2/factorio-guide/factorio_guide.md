# Factorio Mastery Guide

Terminal-first advice from someone who’s launched way too many rockets.

## When You Feel Stuck

```
┌─────────────────────────────────────────┐
│  WHEN YOU FEEL STUCK, ASK:              │
├─────────────────────────────────────────┤
│  □ What's my current bottleneck?        │
│  □ What science am I blocked on?        │
│  □ Do I have enough raw throughput?     │
│  □ Is my power supply stable?           │
│  □ Am I spending too long on defense?   │
└─────────────────────────────────────────┘
```

If you answer those five, you’ll almost always find the next action in under a minute.

---

## 1) The Factorio Mindset

- The factory is never “done” — every build is a draft. The skill is iterating without stalling.
- Bottleneck thinking: your factory speed equals the slowest link. Fix *one* constraint at a time.
- Throughput beats stockpiles: chests hide problems; flowing belts reveal them.
- Organization is optional, but clarity is not: bus/modular layouts make scaling cheap.
- Expand vs. optimize (80/20):
  - If science is blocked: expand production, even if it’s ugly.
  - If everything runs but output is low: trace flow and remove gridlock.
  - If power flickers: fix fuel/power first. Everything else depends on it.

---

## 2) The Progression Arc

```
PHASE 1          PHASE 2           PHASE 3           PHASE 4
Bootstrap   →    Establish    →    Scale        →    Launch
(0–2 hrs)        (2–6 hrs)         (6–15 hrs)        (15+ hrs)
```

### Phase 1 — Bootstrap

- Goal state: automated plates + red science + stable steam power
- Traps: hand-crafting “just a bit longer”, rebuilding too early, coal logistics ignored
- Transition trigger: red runs continuously and you can scale plates quickly

### Phase 2 — Establish

- Goal state: red+green stable, steel online, basic defense automated, tiny mall exists
- Traps: mall first, science later; running out of iron everywhere; letting biters set your pace
- Transition trigger: ~30–60 SPM red/green and steel isn’t precious

### Phase 3 — Scale

- Goal state: blue stable, oil not babysat, circuits scaling, bots start paying back
- Traps: fluid backups, underbuilding green circuits, upgrading everything at once
- Transition trigger: oil system runs unattended and bottlenecks are easy to spot

### Phase 4 — Launch

- Goal state: silo supplied, blue circuits abundant, LDS + rocket fuel steady
- Traps: forgetting satellite, treating rocket as “the end”, not scaling circuits early
- Transition trigger: 100 RCU/LDS/RF without manual crafting

---

## 3) The Science Ladder (Keep It Practical)

### 🔴 Red Science (Automation)

```
INPUTS                BUILD                     OUTPUT
Iron Plates ─► [Gears Asm] ─┐
                            ├─► [Science Asm] ─► 🔴
Copper Plates ──────────────┘
```

- Ratios: 1 gear : 1 copper plate per pack
- Targets: 30 SPM minimum; 60 SPM comfortable
- Why: teaches the core loop — make flow continuous, then scale the bottleneck

### 🟢 Green Science (Logistics)

```
Iron Plates ─► [Gears] ─► [Belts] ─┐
                                  ├─► [Science Asm] ─► 🟢
Iron Plates ─────────► [Inserters] ┘
```

- Targets: 30 SPM minimum; 45–60 SPM comfortable
- Why: makes everything less painful; forces a first real hub (mall)

### 🔷 Blue Science (Chemical)

```
Oil system → Plastic / Sulfur ─┐
                              ├─► Red Circuits ─┐
Steel + gears → Engines ───────┘                 ├─► 🔷 Blue Science
Green circuits ──────────────────────────────────┘
```

- Targets: 15–30 SPM while stabilizing oil; 45+ SPM once cracking is mature
- Why: unlocks the scaling tools (robots) and turns your base into a “growth machine”
- Watch out: oil backs up. Plan cracking (heavy→light→petro) and a dump (solid fuel).

Late sciences (military/purple/yellow/space) aren’t about perfect ratios — they’re about whether your intermediates (steel, circuits, oil) can scale without drama.

---

## 4) Production Chains (Reference)

### Iron

Ore → Plates → (Gears, Steel, Pipes, Ammo, Engines…)

Steel is “5 plates condensed into 1.” Automate it early in Phase 2.

### Copper → Circuits (Critical Path)

Copper Ore → Plates → Wire → Green Circuits → Red → Blue

Rule of thumb: if you think you have enough green circuits, you don’t.

### Oil (The #1 Sticking Point)

See `factorio-guide/assets/layouts/oil_processing_overview.txt`.

---

## 5) Ratios That Matter (Quick Reference)

| Area | Rule of thumb | Why it matters |
|------|---------------|----------------|
| Belts | Yellow 15/s • Red 30/s • Blue 45/s | Everything is feeding belts. |
| Smelting | Stone: 0.3125 plates/s → 48 per yellow belt<br>Steel/Electric: 0.625 plates/s → 24 per yellow belt | Prevents hidden starvation. |
| Circuits | 3 cable assemblers : 2 green circuit assemblers | Greens are a universal bottleneck. |
| Steam | 1 offshore pump → 20 boilers → 40 engines | Brownouts waste time everywhere. |
| Solar | 25 panels : 21 accumulators | Modular late-game power. |

---

## 6) Common Failure Modes & Fixes

| You notice… | The problem is… | Fix by… |
|------------|------------------|---------|
| Everything running but nothing produced | Gridlock or missing output path | Trace the item path; fix first jam; buffer sparingly |
| Constant brownouts | Power or fuel supply behind demand | Fix fuel first, then scale boilers/engines or solar |
| Biters overwhelming you | Pollution reached nests; military isn’t automated | Automate turrets+ammo; clear nests in pollution cloud |
| One resource backs up everywhere | Downstream consumer missing/stalled | Find first non-consuming node and fix it |
| Research crawling | Science underproduced (iron/greens/oil) | Start at labs and walk backward |

---

## 7) Decision Trees

### “Should I rebuild or expand?”

```
Is your base producing the science you need?
    │
    ├─► NO: Don't rebuild. Expand production first.
    │       Ugly but working > pretty but slow
    │
    └─► YES: Is rebuilding blocking progress?
              │
              ├─► NO: Keep playing, rebuild is a trap
              │
              └─► YES: Rebuild ONLY the blocking section
```

### “Should I clear biters or build defenses?”

```
Are nests within your pollution cloud?
    │
    ├─► YES: Clear them. They'll keep attacking.
    │
    └─► NO: Are attacks manageable?
              │
              ├─► YES: Ignore, focus on factory
              │
              └─► NO: Build walls + turrets at chokepoints
                      Don't over-invest in military
```

---

## 8) Layout Patterns (Templates)

- `factorio-guide/assets/layouts/basic_smelting_array.txt`
- `factorio-guide/assets/layouts/main_bus_basics.txt`

Rule: design for upgrades and doubling. Perfection is optional; forward momentum isn’t.

---

## 9) The Launch Checklist

```
┌─────────────────────────────────────────────────────────────┐
│  ROCKET LAUNCH REQUIREMENTS                                 │
├─────────────────────────────────────────────────────────────┤
│  □ Rocket Silo (researched + built)                         │
│  □ 100 Rocket Control Units (blue circuits!)                │
│  □ 100 Low Density Structures (steel, copper, plastic)      │
│  □ 100 Rocket Fuel (light oil → solid fuel → rocket fuel)   │
│  □ 1 Satellite (radar, solar, accumulators, etc.)           │
│                                                             │
│  ⚠  The satellite is often forgotten. Build it early.       │
│                                                             │
│  KEY INSIGHT: Most stalls are blue circuits. Scale early.   │
└─────────────────────────────────────────────────────────────┘
```

The rocket isn’t a boss fight — it’s just three steady lines you haven’t built yet.
*** Add File: factorio-guide/factorio_guide.typ
// Factorio Mastery Guide — Typst starter
// Render with: typst compile factorio-guide/factorio_guide.typ factorio-guide/factorio-guide.pdf

#let colors = (
  primary: rgb("#f4a261"),
  secondary: rgb("#4d7ea8"),
  accent: rgb("#2ecc71"),
  warn: rgb("#e74c3c"),
)

#set page(margin: 18pt)
#set text(font: "Inter", size: 10.5pt)
#set heading(numbering: "1.")

#let section-card(title, body) = block(
  fill: rgb("#101317"),
  radius: 6pt,
  inset: 12pt,
)[
  #text(fill: colors.primary, weight: "bold")[#title]
  #v(8pt)
  #body
]

= Factorio Mastery Guide

#text(fill: rgb("#a8b3bd"))[
Opinionated, practical guidance for staying un-stuck: what to do now, and why.
]

#v(10pt)

== The Factorio Mindset

#section-card("When you feel stuck, ask", [
  - What’s my current bottleneck?
  - What science am I blocked on?
  - Do I have enough raw throughput?
  - Is my power stable?
  - Am I spending too long on defense?
])

== The Progression Arc

#section-card("Phases", [
  *Bootstrap* → *Establish* → *Scale* → *Launch*
  \\
  Use phases as a *flow* check, not a time gate.
])

// TODO: Expand this Typst version to mirror factorio_guide.md content.
