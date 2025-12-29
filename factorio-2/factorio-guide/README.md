# Factorio Mastery Guide (Terminal-First)

This is an opinionated, terminal-native companion for Factorio: it’s built to answer “what should I be doing right now, and why?” without turning into a wiki dump.

## Run

Rich (recommended):

```bash
python3 -m pip install -r factorio-guide/requirements.txt
python3 factorio-guide/factorio_guide.py
```

Pipe the full guide into `less` (keeps colors):

```bash
python3 factorio-guide/factorio_guide.py --all | less -R
```

Quick reference (ratios):

```bash
python3 factorio-guide/factorio_guide.py --quick
```

Jump to a phase:

```bash
python3 factorio-guide/factorio_guide.py --phase 3
```

## No Rich?

If `rich` isn’t installed, the script falls back to printing `factorio-guide/factorio_guide.md`.

## Files

- `factorio-guide/factorio_guide.py`: Rich terminal guide + interactive menu
- `factorio-guide/factorio_guide.md`: Markdown fallback (readable anywhere)
- `factorio-guide/factorio_guide.typ`: Typst starter for a PDF build
- `factorio-guide/assets/layouts/`: ASCII layout templates
