---
version: "alpha"
name: "NVIDIA Power Green"
description: "Design an NVIDIA-inspired high-contrast landing page. Ideal for gpu computing, hardware, tecnologia de alto desempenho, data centers, gaming. AI-ready template."
colors:
  primary: "#000000"
  secondary: "#ffffff"
  tertiary: "#76b900"
  neutral: "#1a1a1a"
  surface: "#bff230"
  accent: "#df6500"
typography:
  h1:
    fontFamily: system-ui
    fontSize: 2.25rem
    fontWeight: 700
  body-md:
    fontFamily: system-ui
    fontSize: 1rem
    fontWeight: 400
  label-caps:
    fontFamily: system-ui
    fontSize: 0.75rem
    fontWeight: 500
rounded:
  sm: 2px
  md: 4px
  lg: 8px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral}"
    rounded: "{rounded.sm}"
    padding: 12px
---

# NVIDIA Power Green — Design System & Architecture

## Overview

Design an NVIDIA-inspired high-contrast landing page. Ideal for gpu computing, hardware, tecnologia de alto desempenho, data centers, gaming. AI-ready template. NVIDIA's green didn't start as a brand color — it started as a statement. When Jensen Huang founded the company in 1993, the GPU was a niche component for gamers who wanted smoother frame rates. The green was loud, almost aggressive, deliberately chosen to cut through the beige-and-gray monotony of 90s computing hardware. It said: this isn't your office PC. This is something else entirely.

Fast-forward three decades and that same green now represents the backbone of artificial intelligence infrastructure. The color carried NVIDIA from gaming peripherals to trillion-dollar market cap without ever getting a rebrand. That's rare. Most tech companies soften their palette as they mature — NVIDIA doubled down. The green got darker, more saturated, more confident. It went from "look at me" to "you already know."

What makes Power Green interesting from a design perspective is its refusal to be neutral. In an industry obsessed with minimalism and safe grays, NVIDIA kept pushing a color that demands attention. It's become shorthand for computational power itself — when you see that green glow, you expect performance numbers that make other hardware look quaint.

- Density: 5/10 — Balanced
- Variance: 4/10 — Moderate
- Motion: 4/10 — Subtle

- **Style:** High-Contrast, Neon Green Accent, Industrial Typography, Sharp Corners, GPU Power
- **Keywords:** nvidia, power green, high-contrast, industrial, sharp corners, GPU, green borders, uppercase nav, Font Awesome, dark/light alternation
- **Era:** 2024-2026 GPU Computing Power
- **Light/Dark:** ✓ Full / ✓ Full

## Colors

- **Preto** (#000000) — Dark surface, primary background
- **Branco** (#ffffff) — Light surface, card backgrounds
- **Verde NVIDIA** (#76b900) — Supporting palette color, pure interactive accent
- **Quase Preto** (#1a1a1a) — Dark surface, primary container background
- **Verde Claro** (#bff230) — Success states, positive indicators
- **Laranja** (#df6500) — Warm accent, call-to-action secondary
- **Cinza** (#a7a7a7) — Secondary text, borders, muted elements
- **Borda** (#5e5e5e) — Extended palette, decorative and component borders

## Typography

- **Display / Hero:** system-ui — Weight 700, tight tracking, used for headline impact
- **Body:** system-ui — Weight 400, 16px/1.6 line-height, max 72ch per line
- **UI Labels / Captions:** system-ui — 0.875rem, weight 500, slight letter-spacing
- **Monospace:** JetBrains Mono — Used for code, metadata, paths, and technical values

Scale:
- Hero: clamp(2.5rem, 5vw, 4rem)
- H1: 2.25rem
- H2: 1.5rem
- Body: 1rem / 1.6
- Small: 0.875rem

## Shapes & Geometry

Base corner radius: 2px. All cards, buttons, badges, and modals use minimal 1-2px border-radius with sharp, engineered corners.

## Technical CSS Implementation

```css
background: #000000;
color: #ffffff;
accent: #76b900;
border: 2px solid #76b900 for CTAs;
border-radius: 2px;
font-family: system-ui, Arial, sans-serif;
font-weight: 700;
text-transform: uppercase for nav;
box-shadow: rgba(0,0,0,0.3) 0px 0px 5px;
```
