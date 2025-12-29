// Factorio Mastery Guide — Typst starter
// Render with:
//   typst compile factorio-guide/factorio_guide.typ factorio-guide/factorio-guide.pdf

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
