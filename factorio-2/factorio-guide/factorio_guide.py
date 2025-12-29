#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent


try:
    from rich import box
    from rich.align import Align
    from rich.console import Console
    from rich.console import Group
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover
    RICH_AVAILABLE = False


PALETTE = {
    "primary": "#f4a261",  # amber/orange (belts, inserters)
    "secondary": "#4d7ea8",  # steel-blue (machines, tech)
    "accent": "#2ecc71",  # green (circuits, success)
    "warn": "#e74c3c",  # red (biters, bottlenecks)
    "muted": "#b7c0c7",
}


@dataclass(frozen=True)
class Phase:
    number: int
    name: str
    time: str
    headline: str
    goal_state: list[str]
    key_unlocks: list[str]
    common_traps: list[str]
    transition_trigger: list[str]


PHASES: list[Phase] = [
    Phase(
        number=1,
        name="Bootstrap",
        time="0–2 hrs",
        headline="Turn handcrafting into flow",
        goal_state=[
            "Stable burner → electric mining",
            "Automated iron + copper plates",
            "Red science running continuously",
            "Power is boring (steady, fueled)",
        ],
        key_unlocks=["Automation", "Logistics", "Steam power", "Labs"],
        common_traps=[
            "Hand-crafting \"just a bit longer\"",
            "Building a perfect layout too early",
            "Ignoring coal logistics for power",
        ],
        transition_trigger=[
            "You can research nonstop on red",
            "You stop waiting on plates/gears",
            "You have space reserved to expand",
        ],
    ),
    Phase(
        number=2,
        name="Establish",
        time="2–6 hrs",
        headline="Organize so scaling is cheap",
        goal_state=[
            "Red + green science stable",
            "Steel production online",
            "Basic defense is automated (turrets + ammo)",
            "A small \"mall\" for belts/inserters/poles",
        ],
        key_unlocks=["Steel", "Oil prep (pumpjacks)", "Military basics", "Trains (optional)"],
        common_traps=[
            "Overbuilding a mall before science",
            "Running out of iron everywhere",
            "Letting biters dictate your tempo",
        ],
        transition_trigger=[
            "You can sustain ~30–60 SPM on red/green",
            "Steel is no longer precious",
            "You have a clear expansion direction",
        ],
    ),
    Phase(
        number=3,
        name="Scale",
        time="6–15 hrs",
        headline="Oil, circuits, and logistics maturity",
        goal_state=[
            "Blue science stable (oil solved)",
            "Red circuits are scaling",
            "Bots start paying back (construction first)",
            "Power upgrades keep ahead of demand",
        ],
        key_unlocks=["Oil processing", "Advanced circuits", "Robotics", "Modules (starter)"],
        common_traps=[
            "Fluid backups with no cracking plan",
            "Underbuilding green circuits (always)",
            "Upgrading everything instead of the bottleneck",
        ],
        transition_trigger=[
            "Your oil system runs without babysitting",
            "Science stalls are traceable and fixable",
            "You can expand mining/smelting quickly",
        ],
    ),
    Phase(
        number=4,
        name="Launch",
        time="15+ hrs",
        headline="Rocket parts are just another supply chain",
        goal_state=[
            "Rocket silo built and supplied",
            "Blue circuits are abundant",
            "Low density structures are steady",
            "Rocket fuel is automated (light oil pipeline)",
        ],
        key_unlocks=["Rocket silo", "Utility/Production science", "Beacons (optional)", "Megabase (optional)"],
        common_traps=[
            "Forgetting the satellite",
            "Treating rockets as \"endgame\" instead of a new line",
            "Not scaling circuits early enough",
        ],
        transition_trigger=[
            "You can build 100 RCU/LDS/RF without manual craft",
            "The factory runs while you plan, not vice versa",
        ],
    ),
]


def _assets_dir() -> Path:
    return Path(__file__).resolve().parent / "assets"


def _read_asset(rel_path: str) -> str:
    path = _assets_dir() / rel_path
    return path.read_text(encoding="utf-8")


def _title_panel() -> Panel:
    title = Text("FACTORIO MASTERY GUIDE", style=f"bold {PALETTE['primary']}")
    subtitle = Text(
        "A terminal-native companion for staying un-stuck: what to do now, and why.",
        style=PALETTE["muted"],
    )
    body = Align.center(Text.assemble(title, "\n", subtitle), vertical="middle")
    return Panel(body, border_style=PALETTE["secondary"], box=box.HEAVY)


def _section_panel(title: str, content, *, border: str = "secondary") -> Panel:
    return Panel(content, title=title, border_style=PALETTE[border], box=box.HEAVY)


def render_mindset() -> list[object]:
    checklist = dedent(
        """
        ┌─────────────────────────────────────────┐
        │  WHEN YOU FEEL STUCK, ASK:              │
        ├─────────────────────────────────────────┤
        │  □ What's my current bottleneck?        │
        │  □ What science am I blocked on?        │
        │  □ Do I have enough raw throughput?     │
        │  □ Is my power supply stable?           │
        │  □ Am I spending too long on defense?   │
        └─────────────────────────────────────────┘
        """
    ).strip("\n")

    md = Markdown(
        dedent(
            """
            You’re not building a base — you’re building a *process*.

            - **The factory is never “done.”** Every build is a draft. The skill is iterating without stalling.
            - **Bottleneck thinking:** your factory speed equals the slowest link. Fix *one* constraint at a time.
            - **Throughput beats stockpiles:** chests hide problems; flowing belts reveal them.
            - **Organization is a force multiplier:** buses/modularity reduce cognitive load and make scaling cheap.
            - **Expand vs. optimize (80/20):**
              - If research is blocked: expand production, even if it’s ugly.
              - If everything runs but feels “stuck”: trace flow and remove gridlock.
              - If power flickers: fix fuel/power first — everything else depends on it.
            """
        ).strip()
    )

    checklist_panel = Panel(
        Text(checklist, style=PALETTE["primary"]),
        title="Mental Checklist",
        border_style=PALETTE["primary"],
        box=box.DOUBLE,
    )

    return [
        _section_panel("1) The Factorio Mindset", md),
        checklist_panel,
    ]


def render_progression_arc(phase: int | None = None) -> list[object]:
    timeline = Text(
        dedent(
            """
            PHASE 1          PHASE 2           PHASE 3           PHASE 4
            Bootstrap   →    Establish    →    Scale        →    Launch
            (0–2 hrs)        (2–6 hrs)         (6–15 hrs)        (15+ hrs)
            """
        ).strip(),
        style=PALETTE["secondary"],
    )

    table = Table(box=box.SIMPLE_HEAVY, expand=True, pad_edge=False)
    table.add_column("Phase", style=f"bold {PALETTE['primary']}", no_wrap=True)
    table.add_column("Goal State", style=PALETTE["muted"])
    table.add_column("Common Traps", style=PALETTE["warn"])
    table.add_column("Transition Trigger", style=PALETTE["accent"])

    phases = [p for p in PHASES if phase in (None, p.number)]
    for p in phases:
        table.add_row(
            f"{p.number}. {p.name}\n[{p.time}]",
            "\n".join(f"• {x}" for x in p.goal_state),
            "\n".join(f"• {x}" for x in p.common_traps),
            "\n".join(f"• {x}" for x in p.transition_trigger),
        )

    return [
        _section_panel("2) The Progression Arc", timeline),
        table,
        Panel(
            Markdown(
                "Tip: phases aren’t time gates. The trigger is *flow*: when the current science runs continuously and you can scale inputs quickly, move on."
            ),
            border_style=PALETTE["muted"],
            box=box.SQUARE,
        ),
    ]


def _science_card(
    *,
    title: str,
    recipe: str,
    ratios: list[str],
    rates: list[str],
    why: list[str],
    warning: str | None = None,
) -> Panel:
    parts: list[object] = [
        Text(recipe.strip("\n"), style=PALETTE["secondary"]),
        Rule(style=PALETTE["muted"]),
        Markdown(
            dedent(
                f"""
                **Ratios (keep it simple):**
                {chr(10).join(f"- {r}" for r in ratios)}

                **Production targets:**
                {chr(10).join(f"- {r}" for r in rates)}

                **Why this science matters:**
                {chr(10).join(f"- {w}" for w in why)}
                """
            ).strip()
        ),
    ]
    if warning:
        parts.append(
            Panel(
                Text(warning, style=f"bold {PALETTE['warn']}"),
                title="Watch Out",
                border_style=PALETTE["warn"],
                box=box.SQUARE,
            )
        )
    return _section_panel(title, Align.left(Group(*parts)), border="primary")


def render_science_ladder() -> list[object]:
    intro = Markdown(
        dedent(
            """
            The game’s real progression is *science throughput*. Every time you add a science, you’re adding:
            new inputs, new bottlenecks, and usually one new “hard” system (oil, robots, modules).

            Don’t chase perfect ratios. Chase **stable research**, then scale the bottleneck.
            """
        ).strip()
    )

    red = _science_card(
        title="🔴 Red Science (Automation)",
        recipe=dedent(
            """
            INPUTS                BUILD                     OUTPUT
            Iron Plates ─► [Gears Asm] ─┐
                                      ├─► [Science Asm] ─► 🔴
            Copper Plates ─────────────┘
            """
        ),
        ratios=[
            "1 gear : 1 copper plate per pack",
            "Starter: 1 gear assembler feeding 1 science assembler",
        ],
        rates=[
            "Minimum viable: ~30 SPM (0.5/sec) to keep moving",
            "Comfortable: ~60 SPM (1/sec) if you like fast tech",
        ],
        why=[
            "Unlocks the idea that *automation is the game*",
            "Sets your first real constraint: iron throughput",
        ],
    )

    green = _science_card(
        title="🟢 Green Science (Logistics)",
        recipe=dedent(
            """
            INPUTS                         BUILD                       OUTPUT
            Iron Plates ─► [Gears] ─► [Belts] ─┐
                                             ├─► [Science Asm] ─► 🟢
            Iron Plates ─────────► [Inserters] ┘
            """
        ),
        ratios=[
            "Belts + inserters are iron-hungry: expect iron to be the limiter",
            "If green is slow, check gears → inserters first (classic choke)",
        ],
        rates=[
            "Minimum viable: 30 SPM (your first “real base”)",
            "Comfortable: 45–60 SPM (good pacing for blue prep)",
        ],
        why=[
            "Unlocks belts/inserters upgrades that reduce friction everywhere",
            "Forces you to build your first small supply hub (mall)",
        ],
        warning="If you’re rebuilding for aesthetics here, you’re probably stalling progress. Expand first.",
    )

    blue = _science_card(
        title="🔷 Blue Science (Chemical)",
        recipe=dedent(
            """
            THE BLUE SCIENCE TRIANGLE (WHY IT HURTS)

              Oil system → Plastic / Sulfur
                    │            │
                    ├─────► Red Circuits
                    │
            Steel + Gears → Engines
                    │
                    └─────► 🔷 Blue Science
            """
        ),
        ratios=[
            "Treat oil as a *system*, not a recipe: you must handle byproducts",
            "Blue’s true bottleneck is usually green circuits → red circuits → engines",
        ],
        rates=[
            "Minimum viable: 15–30 SPM while you stabilize oil",
            "Comfortable: 45+ SPM once cracking + circuits are scaling",
        ],
        why=[
            "Unlocks the tools that make scaling easy (bots, advanced logistics)",
            "Turns your base from “working” into “self-expanding”",
        ],
        warning="If petroleum backs up or runs dry, don’t guess. Add cracking and a dump (solid fuel) so the system keeps moving.",
    )

    late = _section_panel(
        "Late Sciences (Military / Production / Utility / Space)",
        Markdown(
            dedent(
                """
                You don’t need perfect setups — you need *a clear next constraint*.

                - **Military:** buy time. Automate turrets/ammo, clear nests in your pollution cloud, then go back to science.
                - **Production (purple):** expensive “industry” items; build it when you can mass-produce steel, rails, furnaces.
                - **Utility (yellow):** robotics + high-tier components; the “are your intermediates scalable?” exam.
                - **Space/rocket:** 3 big lines (RCU, LDS, Rocket Fuel). Most stalls are **blue circuits** → start scaling them early.
                """
            ).strip()
        ),
        border="secondary",
    )

    return [_section_panel("3) The Science Ladder", intro), red, green, blue, late]


def render_production_chains() -> list[object]:
    iron = Text(
        dedent(
            """
            IRON (THE FOUNDATION)
            Ore → Plates → (Gears, Steel, Pipes, Ammo, Engines…)

            - Plates are the default constraint.
            - Steel is “5 plates condensed into 1”: automate it early in Phase 2.
            """
        ).strip(),
        style=PALETTE["secondary"],
    )

    copper = Text(
        dedent(
            """
            COPPER → CIRCUITS (THE CRITICAL PATH)
            Copper Ore → Plates → Wire → Green Circuits → Red → Blue

            Rule of thumb: if you think you have enough green circuits, you don’t.
            """
        ).strip(),
        style=PALETTE["secondary"],
    )

    oil = Text(_read_asset("layouts/oil_processing_overview.txt").rstrip("\n"), style=PALETTE["secondary"])

    circuits_table = Table(box=box.SIMPLE, expand=True)
    circuits_table.add_column("Chain", style=f"bold {PALETTE['primary']}", no_wrap=True)
    circuits_table.add_column("What usually breaks", style=PALETTE["warn"])
    circuits_table.add_column("Fix mindset", style=PALETTE["accent"])
    circuits_table.add_row(
        "Green circuits",
        "Copper cable starvation, not enough copper plates",
        "Scale copper smelting and feed cable locally",
    )
    circuits_table.add_row(
        "Red circuits",
        "Plastic/oil instability + green circuit demand spike",
        "Stabilize petroleum, then add dedicated green circuits",
    )
    circuits_table.add_row(
        "Blue circuits",
        "Everything (reds + sulfuric acid + greens) is tight",
        "Build it like a “factory within a factory” with room to double",
    )

    return [
        _section_panel("4) The Production Chains", iron),
        _section_panel("Copper & Circuits", copper, border="primary"),
        _section_panel("Oil Processing (The #1 Sticking Point)", oil, border="warn"),
        _section_panel("Circuit Cascade (What to Scale First)", circuits_table, border="accent"),
    ]


def render_ratios_quick() -> list[object]:
    table = Table(
        title="PRODUCTION RATIOS — THE ESSENTIAL NUMBERS",
        box=box.DOUBLE_EDGE,
        expand=True,
        title_style=f"bold {PALETTE['primary']}",
    )
    table.add_column("Area", style=f"bold {PALETTE['secondary']}", no_wrap=True)
    table.add_column("Rule of Thumb", style=PALETTE["muted"])
    table.add_column("Why it matters", style=PALETTE["accent"])

    table.add_row(
        "Belts",
        "Yellow 15/s • Red 30/s • Blue 45/s",
        "Throughput math starts here; everything else is feeding belts.",
    )
    table.add_row(
        "Smelting",
        "Stone furnace: 0.3125 plates/s → 48 for a yellow belt\nSteel/Electric: 0.625 plates/s → 24 for a yellow belt",
        "Saturating belts prevents “mystery starvation” downstream.",
    )
    table.add_row(
        "Circuits",
        "3 cable assemblers : 2 green circuit assemblers (same tier)",
        "Greens are a universal input; they’re almost always the bottleneck.",
    )
    table.add_row(
        "Power (steam)",
        "1 offshore pump → 20 boilers → 40 steam engines",
        "Steam is your early backbone; brownouts waste time everywhere.",
    )
    table.add_row(
        "Power (solar)",
        "25 solar panels : 21 accumulators (≈0.84:1)",
        "A clean, modular late-game power block.",
    )

    return [
        _section_panel(
            "5) Ratios That Matter (Quick Reference)",
            Markdown("If you only look at one page mid-run, make it this one."),
            border="primary",
        ),
        table,
    ]


def render_failure_modes() -> list[object]:
    table = Table(box=box.SIMPLE_HEAVY, expand=True)
    table.add_column("You notice…", style=f"bold {PALETTE['primary']}")
    table.add_column("The problem is…", style=PALETTE["warn"])
    table.add_column("Fix by…", style=PALETTE["accent"])

    rows = [
        (
            "Everything is running but nothing is produced",
            "Inserter/belt gridlock or a missing output path",
            "Trace the item path; fix the first jam; add splitters/buffers sparingly",
        ),
        (
            "Constant brownouts / flickering lights",
            "Power generation or fuel delivery is behind demand",
            "Fix coal supply first, then scale boilers/engines or add solar",
        ),
        (
            "Biters are overwhelming you",
            "Pollution reached nests; military isn’t automated",
            "Automate turrets + ammo; clear nests inside pollution cloud",
        ),
        (
            "One resource backs up everywhere",
            "A downstream consumer is missing or stalled",
            "Work forward until consumption stops; fix that node, not the whole line",
        ),
        (
            "Research crawls",
            "Science packs are underproduced (usually iron/greens/oil)",
            "Start at the labs and walk backward: what pack is missing and why?",
        ),
    ]
    for r in rows:
        table.add_row(*r)

    return [
        _section_panel(
            "6) Common Failure Modes & Fixes",
            Markdown("Diagnosis patterns are faster than memorizing layouts."),
            border="warn",
        ),
        table,
    ]


def render_decision_trees() -> list[object]:
    rebuild = Text(
        dedent(
            """
            "SHOULD I REBUILD OR EXPAND?"

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
            """
        ).strip("\n"),
        style=PALETTE["secondary"],
    )

    biters = Text(
        dedent(
            """
            "SHOULD I CLEAR BITERS OR BUILD DEFENSES?"

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
            """
        ).strip("\n"),
        style=PALETTE["secondary"],
    )

    return [
        _section_panel("7) The Decision Trees", rebuild, border="primary"),
        _section_panel("Defense Decisions", biters, border="warn"),
    ]


def render_layout_patterns() -> list[object]:
    smelt = Text(_read_asset("layouts/basic_smelting_array.txt").rstrip("\n"), style=PALETTE["secondary"])
    bus = Text(_read_asset("layouts/main_bus_basics.txt").rstrip("\n"), style=PALETTE["secondary"])

    tips = Markdown(
        dedent(
            """
            Layout isn’t about perfection — it’s about *future moves being easy*.

            - Leave room to double (then double again).
            - Separate “spine” (bus/rails) from “organs” (production blocks).
            - Upgrade only when it removes a bottleneck (not because you unlocked it).
            """
        ).strip()
    )

    return [
        _section_panel("8) Layout Patterns (Templates)", tips, border="secondary"),
        _section_panel("Basic Smelting Array", smelt, border="primary"),
        _section_panel("Main Bus Basics", bus, border="primary"),
    ]


def render_launch_checklist() -> list[object]:
    checklist = dedent(
        """
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
        """
    ).strip("\n")

    md = Markdown(
        dedent(
            """
            The rocket is not a boss fight — it’s a supply chain you haven’t built yet.

            Build three steady lines (RCU, LDS, Rocket Fuel), then let the factory do the waiting.
            """
        ).strip()
    )

    return [
        _section_panel("9) The Launch Checklist", md, border="accent"),
        Panel(Text(checklist, style=PALETTE["primary"]), border_style=PALETTE["primary"], box=box.DOUBLE),
    ]


SECTIONS = [
    ("mindset", "The Factorio Mindset", render_mindset),
    ("progression", "The Progression Arc", render_progression_arc),
    ("science", "The Science Ladder", render_science_ladder),
    ("chains", "The Production Chains", render_production_chains),
    ("ratios", "Ratios That Matter", render_ratios_quick),
    ("failure", "Common Failure Modes", render_failure_modes),
    ("decisions", "Decision Trees", render_decision_trees),
    ("layouts", "Layout Patterns", render_layout_patterns),
    ("launch", "Launch Checklist", render_launch_checklist),
]


def _print_section(console: Console, section_key: str, *, phase: int | None = None) -> None:
    for key, _, fn in SECTIONS:
        if key != section_key:
            continue
        if fn is render_progression_arc:
            renderables = fn(phase=phase)  # type: ignore[arg-type]
        else:
            renderables = fn()
        for r in renderables:
            console.print(r)
            console.print()
        return
    raise SystemExit(f"Unknown section: {section_key}")


def _print_all(console: Console) -> None:
    console.print(_title_panel())
    console.print()
    for idx, (key, title, _) in enumerate(SECTIONS, start=1):
        console.print(Rule(f"[{PALETTE['muted']}]{idx}. {title}[/]", style=PALETTE["muted"]))
        _print_section(console, key)


def _menu(console: Console) -> None:
    console.print(_title_panel())
    console.print()

    menu = Table(box=box.SIMPLE, expand=True)
    menu.add_column("Key", style=f"bold {PALETTE['primary']}", no_wrap=True)
    menu.add_column("Section", style=PALETTE["muted"])

    for idx, (key, title, _) in enumerate(SECTIONS, start=1):
        menu.add_row(str(idx), f"{title}  [{key}]")
    menu.add_row("A", "Print everything (good for `| less -R`)")
    menu.add_row("Q", "Quit")

    while True:
        console.print(menu)
        choice = Prompt.ask(
            "Choose a section",
            default="1",
            show_default=True,
        ).strip()

        if choice.lower() in {"q", "quit", "exit"}:
            return
        if choice.lower() in {"a", "all"}:
            console.clear()
            _print_all(console)
            return

        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(SECTIONS):
                console.clear()
                _print_section(console, SECTIONS[idx - 1][0])
                Prompt.ask("Press Enter to return to menu", default="")
                console.clear()
                continue

        key_match = choice.lower()
        keys = {k for k, _, _ in SECTIONS}
        if key_match in keys:
            console.clear()
            _print_section(console, key_match)
            Prompt.ask("Press Enter to return to menu", default="")
            console.clear()
            continue

        console.print(Panel("Invalid choice. Pick 1–9, a section key, A, or Q.", border_style=PALETTE["warn"]))


def _print_plain(markdown_path: Path) -> None:
    if markdown_path.exists():
        sys.stdout.write(markdown_path.read_text(encoding="utf-8"))
        return
    sys.stdout.write(
        "Rich is not installed, and the Markdown fallback was not found.\n"
        "Install rich with: python3 -m pip install rich\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="factorio_guide.py",
        description="Terminal-native Factorio mastery guide (Rich UI + quick reference).",
    )
    parser.add_argument("--list", action="store_true", help="List available sections and exit.")
    parser.add_argument("--section", choices=[k for k, _, _ in SECTIONS], help="Jump to a specific section.")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4], help="Jump to a specific game phase.")
    parser.add_argument("--quick", action="store_true", help="Show quick ratio table (alias for --section ratios).")
    parser.add_argument("--all", action="store_true", help="Print the full guide (good for piping to less).")
    parser.add_argument("--plain", action="store_true", help="Force plain text (prints the Markdown fallback).")
    args = parser.parse_args(argv)

    markdown_fallback = Path(__file__).resolve().with_suffix(".md")

    if args.plain or not RICH_AVAILABLE:
        _print_plain(markdown_fallback)
        return 0 if markdown_fallback.exists() else 1

    console = Console()

    if args.list:
        for idx, (key, title, _) in enumerate(SECTIONS, start=1):
            console.print(f"{idx}. {title} ({key})")
        return 0

    if args.quick and not args.section:
        args.section = "ratios"

    if args.phase and not args.section:
        args.section = "progression"

    if args.all:
        _print_all(console)
        return 0

    if args.section:
        console.print(_title_panel())
        console.print()
        _print_section(console, args.section, phase=args.phase)
        return 0

    # Default behavior: interactive menu when in a TTY, otherwise print all.
    if sys.stdin.isatty() and sys.stdout.isatty():
        _menu(console)
        return 0

    _print_all(console)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
