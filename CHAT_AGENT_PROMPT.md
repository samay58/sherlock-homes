# Prompt for Chat Agent: Sherlock Homes Technical Assessment

Copy everything below the line into Chat Agent, along with the contents of `TECHNICAL_EXPLAINER.md` as context.

---

## PROMPT

You are an expert software architect and real estate technology consultant. I'm sharing with you a comprehensive technical explainer of my property intelligence app called Sherlock Homes. The app scrapes rental listings, enriches them with NLP and computer vision, scores them against weighted buyer criteria, and surfaces personalized matches with alerts.

The app was originally built for SF home purchases and I've recently adapted it for NYC rental search. My partner and I are looking for a place in NYC (Williamsburg, nice Brooklyn neighborhoods, West Village, SoHo, Flatiron, Gramercy, Chelsea, East Village) for an April/May 2026 move-in. Budget is $7-9K/month. Must-haves: pet friendly, great natural light, gym access, character (not a soulless high-rise box), good kitchen.

I need you to do a thorough, impartial technical assessment and return a structured set of instructions that I can hand back to my coding agent (Claude Code) to implement. Be specific, opinionated, and prioritized. Don't sugarcoat. I want this thing to actually find us an incredible place to live, not just be a technically interesting project.

Here's what I need from you:

### 1. Architecture Assessment
- Review the overall system architecture, data flow, and component responsibilities
- Identify any architectural anti-patterns, unnecessary complexity, or missing abstractions
- Assess whether the current architecture can scale to the task (finding the best NYC rental)

### 2. Scoring Engine Deep Dive
- The scoring engine has 17 weighted criteria totaling 126 points, but 4 criteria (34 points / 27%) have no implementation. Assess the impact and propose how to wire them in
- Evaluate whether the current NLP keyword-matching approach is sufficient or if something more sophisticated is needed
- Review the tier thresholds (Exceptional 100+, Strong 88+, Interesting 76+) in light of the 34 unreachable points
- Assess the NLP multiplier system (1.5x for light, 1.8x for pet, etc.) and whether the weights make sense for NYC rentals
- The geospatial module is entirely SF-locked (hardcoded SF streets, freeways, fire stations). Propose a practical fix for NYC

### 3. Data Quality and Coverage
- Only 7% of listings (24/334) have descriptions after enrichment. This is the biggest bottleneck for scoring quality. Propose a strategy to maximize description coverage
- Detail API calls are wasted on duplicate listings before deduplication. Design a fix
- Assess whether Zillow alone is sufficient for NYC rental search or if additional sources are needed. Be specific about which sources and how to integrate them
- The neighborhood tagging required multiple bug fixes (generic borough names, detail enrichment overrides). Is the current approach robust or fragile?

### 4. NYC-Specific Improvements
- What NYC-specific intelligence is missing that would meaningfully improve listing quality assessment?
- Think about: subway proximity, floor level, building amenities, neighborhood character, noise patterns, seasonal availability
- What keywords or signals are particularly important for NYC rentals that may not be well-covered?

### 5. Prioritized Implementation Plan
Return a numbered list of concrete implementation tasks, ordered by impact on finding a great apartment. For each task:
- **What**: Clear description of the change
- **Where**: Specific files to modify
- **How**: Implementation approach (enough detail for a coding agent to execute)
- **Impact**: What this unblocks or improves
- **Effort**: Rough complexity (small / medium / large)

Group them into:
- **Phase 1: Fix the broken stuff** (things that are actively wrong)
- **Phase 2: Maximize signal quality** (getting more and better data)
- **Phase 3: Next-level intelligence** (things that would make this genuinely exceptional)

### 6. Creative Ideas
- What would make this app genuinely exceptional at finding a dream apartment, beyond fixing bugs?
- Think about what a human apartment hunter does that this app doesn't
- Consider: timing intelligence, broker relationship signals, building reputation, neighborhood vibe matching, commute optimization, deal quality assessment

### Constraints for Your Response
- Be concrete and implementation-specific. "Improve NLP" is useless. "Add 15 pet-related keywords to extract_flags() and create a pet_friendly scoring method in _score_listing()" is useful.
- Reference specific files, functions, and line numbers from the explainer.
- Consider API cost implications (ZenRows charges per call, OpenAI charges per token).
- The coding agent (Claude Code) will implement your instructions, so write them as clear engineering specs.
- Prioritize ruthlessly. I care about finding an amazing apartment, not building a perfect system. What gets me closest to that goal fastest?
- Don't be precious about the existing code. If something should be ripped out and rewritten, say so.

The technical explainer document follows below.
