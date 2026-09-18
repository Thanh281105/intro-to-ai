# GUI Design Architecture & Visual System

The Sokoban Pygame GUI was completely redesigned to deliver an indie puzzle game experience paired with an academic AI telemetry platform. The board remains the visual hero (~68% visual attention), surrounded by structured slate HUD cards and an interactive bottom replay timeline.

## 1. Resolution & Window Layout
- **Desktop Dimensions**: 1280 × 760 pixels (16:9 ratio).
- **Top Navigation Bar**: Brand identity (`SOKOBAN AI` / `SOKOBAN DUEL`), mode subtitle chip, and status pill badges (`ALGO`, `MAP`, `LEADER`, `STATUS`).
- **Hero Playfield**: Centered inside a warm wood-stone container (`#201912`) with rounded corners, 1px inner bevel highlight (`#624E38`), brass corner rivets, and a soft 140-alpha drop shadow.
- **Right Telemetry Panel**: Elevated slate cards with 12px border radius, subtle borders (`#28384C`), and 16px grid alignment:
  - *Search Overview / Duel Scoreboard*: High-impact 2×2 metric pills or dual agent scorecards with "VS" divider and leader banner.
  - *Performance Telemetry / Round Progress*: Mini horizontal visual bars for Expanded Nodes, Generated Nodes, and Frontier size, alongside microsecond runtime badges.
  - *Controls Guide / Ownership Identity*: Interactive keycap badges (`[SPACE]`, `[ARROWS]`, `[R]`, `[ESC]`) and box ownership legend.
- **Bottom Replay Timeline**: Step counter (`STEP 03 / 07`), interactive progress scrubber with glowing knob and discrete step ticks, plus vector playback buttons (`[◀] [▶/❚❚] [▶] [↺]`).

## 2. Color Palette & Visual Tokens
- **Background**: Deep desaturated navy-charcoal (`#0F141C`) with elevated dark slate cards (`#17202D`, `#1D2939`).
- **Typography**: High contrast white-silver (`#F6F8FC`), secondary silver-blue (`#96A5B9`), and dim labels (`#697A92`) rendered with crisp system sans fallbacks (`segoeui`, `sfprodisplay`, `arial`).
- **Floor Paving**: Warm sandstone (`#EEE2CC` light, `#E5D8BE` shaded) with subtle 1px mortar joints (`#D6C8AE`), top-left inner highlights, and deterministic fine stone flecks.
- **Masonry Walls**: Olive-stone foundation (`#5E5846`) with staggered two-course brick courses, top/left 3D bevel highlights (`#8A826A`), bottom/right shadows (`#363226`), and dark mortar joints (`#221F16`).
- **Wooden Crates**: Honey amber body (`#DA7E2A`), dark plank frame (`#9A5218`), recessed center panel (`#BE6A1C`), dimensional diagonal X-brace, top highlight rim (`#F6AA4E`), and polished brass corner rivets (`#EBBE69`).
- **Goals & Targets**: Concentric crimson-coral target rings (`#E4584A`, `#FC8678`) etched into the floor, centered with a golden jewel diamond (`#FFD664`).
- **Box on Goal**: Radiant golden halo rim (`#FFDA4C`), inner gold double border, and gleaming victory star/diamond emblem.

## 3. Directional Player & Competitive Multi-Agent Identity
- **Single Replay Player**: Solo adventurer with charcoal cap, vibrant teal jacket (`#2896BA`), belt with brass buckle, and an expedition backpack with leather straps visible when facing North.
- **4-Way Orientation**: Character face, cap visor, boots, and pack dynamically reflect the last move direction (`North`, `East`, `South`, `West`).
- **Competitive Agents**:
  - **Agent 1 (A\*)**: Cyan-teal outfit (`#2AA2C6`), navy cap, and white/cyan "1" chest shield badge.
  - **Agent 2 (GBFS)**: Terracotta-coral outfit (`#E4563C`), maroon cap, and white/coral "2" chest shield badge.
- **Box Ownership Encoding**:
  - *A1 Owned Box*: Wooden crate + cyan-teal double border (`#2AA2C6`) + top-left "A1" corner shield badge.
  - *A2 Owned Box*: Wooden crate + coral-red double border (`#E4563C`) + top-right "A2" corner shield badge.
  - *Neutral Box*: Standard wooden crate without owner badge.
  - Dual visual cues (border geometry + alphanumeric shield badges) guarantee unambiguous identification in grayscale and high-glare projection environments.

## 4. Performance & Deterministic Asset Generation
All tile, wall, crate, goal, and character surfaces are procedurally constructed and cached in `_SPRITE_CACHE` upon first render. Zero dynamic texture generation occurs in the per-frame render loop, comfortably exceeding the 60 FPS target on standard desktop hardware.
