---
name: design
description: >
  UX and visual design system for the rag-docs web UI (frontend/, Vite + React +
  TypeScript, CSS modules, no UI kit). Use when designing, building or reviewing
  any frontend screen or component: tokens, layout, components, states,
  accessibility and copy rules, plus a review checklist. Modern, responsive,
  minimal.
---

# rag-docs design system

The design rules for `frontend/`. The frontend-agent follows them, and the
architect cites them in specs. If a spec conflicts with this skill, the spec
wins; amend this file in the same spec.

## Philosophy: a quiet tool

The user brings a document and a question. The UI exists to get them to an
answer they can trust, and then it gets out of the way.

1. **Content first.** The answer and its sources are the hero. Chrome (borders,
   backgrounds, icons, badges) is added only when it carries information.
2. **One primary action per view.** Exactly one filled accent button is visible
   at a time ("Subir PDF", "Preguntar"). Everything else is secondary or ghost.
3. **Hierarchy from type and space, not colour.** Size, weight and whitespace
   separate things before borders do. Accent colour marks interaction only:
   links, the primary button, focus, the active nav item.
4. **Every request has four states: idle, loading, success and error.** Each
   one is designed. A blank screen or a raw stack trace is a bug.
5. **Mobile first, fluid up.** Design at 360 px, then let it breathe. No
   horizontal page scroll at any width.
6. **Few dependencies.** React plus CSS modules and the tokens below. No
   component library, CSS framework, icon font or web font. Inline SVG for the
   handful of icons needed.
7. **Motion only explains state change.** Use 120–200 ms ease-out fades or
   slides for things that appear (new message, error). Never decorative. Honour
   `prefers-reduced-motion`.

What "simplistic" excludes: hero banners, gradients, glassmorphism, drop
shadows on everything, emoji in UI copy, tooltips that hide required
information, modals for things that fit inline, settings nobody asked for.

## Tokens

Defined once in `src/styles/tokens.css` (imported by `src/index.css`).
Components use `var(--…)` only. Hex values inside component CSS are a review
failure. Light and dark follow `prefers-color-scheme`. Every text/background
pair below meets WCAG AA (≥ 4.5:1 for body text, ≥ 3:1 for large text and UI
boundaries).

```css
:root {
  color-scheme: light dark;

  /* Surfaces */
  --bg: #fafafa;
  --surface: #ffffff;
  --surface-2: #f4f4f5;
  --border: #e4e4e7;
  --border-strong: #a1a1aa; /* inputs: 3:1 against --surface */

  /* Text */
  --text: #18181b;
  --text-muted: #52525b;
  --text-on-accent: #ffffff;

  /* Interaction */
  --accent: #4f46e5;
  --accent-hover: #4338ca;
  --accent-soft: #eef2ff;
  --focus: #4f46e5;

  /* Status: always paired with text or an icon, never colour alone */
  --ok: #15803d;
  --ok-soft: #f0fdf4;
  --warn: #b45309;
  --warn-soft: #fffbeb;
  --danger: #b91c1c;
  --danger-soft: #fef2f2;

  /* Type */
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  --text-xs: 0.75rem;   /* 12 meta */
  --text-sm: 0.875rem;  /* 14 secondary, labels */
  --text-md: 1rem;      /* 16 body, inputs (16 avoids iOS zoom) */
  --text-lg: 1.25rem;   /* 20 section titles */
  --text-xl: 1.5rem;    /* 24 page title */
  --leading: 1.55;

  /* Space: 4 px base */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;

  /* Shape */
  --radius-sm: 6px;   /* inputs, buttons */
  --radius-md: 10px;  /* cards, messages */
  --radius-pill: 999px;
  --shadow-1: 0 1px 2px rgb(0 0 0 / 0.05); /* the only shadow; for floating composer */

  /* Layout */
  --content-max: 760px; /* reading width */
  --shell-max: 1120px;
  --header-h: 56px;

  --ease: cubic-bezier(0.2, 0, 0, 1);
  --dur: 160ms;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0b0b0e;
    --surface: #18181b;
    --surface-2: #232328;
    --border: #2e2e33;
    --border-strong: #71717a;
    --text: #fafafa;
    --text-muted: #a1a1aa;
    --text-on-accent: #0b0b0e;
    --accent: #818cf8;
    --accent-hover: #a5b4fc;
    --accent-soft: #1e1b4b;
    --focus: #a5b4fc;
    --ok: #4ade80;
    --ok-soft: #052e16;
    --warn: #fbbf24;
    --warn-soft: #2a1a03;
    --danger: #f87171;
    --danger-soft: #2a0b0b;
    --shadow-1: none;
  }
}
```

Use only these values. If a new token is needed, add it here and in
`tokens.css` in the same change, with its contrast pair checked.

## Base styles (`src/index.css`)

- `body`: `background: var(--bg)`, `color: var(--text)`,
  `font: var(--text-md)/var(--leading) var(--sans)`, antialiased,
  `min-width: 320px`, `margin: 0`.
- `*, *::before, *::after { box-sizing: border-box }`.
- `:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px }`.
  Never `outline: none` without a visible replacement.
- `[hidden] { display: none !important }`.
- `.visually-hidden` utility for screen-reader-only labels.
- `@media (prefers-reduced-motion: reduce)` sets transitions and animations to
  `none`.

## Layout

- **App shell:** a sticky top bar (`--header-h`) holds the product name on the
  left, the nav (Subir PDF · Preguntar) and the backend status on the right. Below it, a
  single centred column of `max-width: var(--content-max)` with
  `padding-inline: var(--space-4)`. There is no sidebar; on mobile the nav
  stays in the top bar as text links. Use a hamburger only if there are more
  than three entries.
- **Breakpoints** (min-width, mobile first): `640px` (sm) and `1024px` (lg).
  Most screens need none; prefer `clamp()`, `flex-wrap` and
  `grid-template-columns: repeat(auto-fit, minmax(…, 1fr))`.
- **Vertical rhythm:** `--space-5` between sections and `--space-3` inside a
  group. Page padding is `--space-5` top and `--space-7` bottom.
- **Ask view:** the conversation scrolls. The composer (question input + Preguntar)
  is pinned to the bottom of the viewport, inside the content column, using
  `position: sticky; bottom: 0` with a `--bg` backdrop and `--shadow-1`.
- **File names:** snake_case per the Google TypeScript Style Guide
  (`ask_view.tsx`, `ask_view.module.css`); component symbols stay
  `UpperCamelCase`.

## Components

Each is one snake_case `.tsx` file plus a `.module.css` file in `src/components/`. Keep
the API small and the props typed. Use no `className` passthrough unless a
layout needs it.

| Component | Rules |
|---|---|
| `Button` | Variants `primary` (accent fill), `secondary` (surface + `--border-strong`), `ghost` (text only). Height 40 px (44 px touch target on coarse pointers), `--radius-sm`, weight 600. `loading` prop shows an inline spinner, keeps the width and sets `aria-busy`. Disabled uses `opacity: .5` plus `cursor: not-allowed` and keeps the label. |
| `Field` | Label above the control (never placeholder-only), optional hint below in `--text-muted --text-sm`, error below in `--danger` with `aria-describedby` and `aria-invalid`. Inputs are 16 px text, `--border-strong`, `--radius-sm`, and show focus via the accent border plus the outline. |
| `Card` | `--surface`, 1 px `--border`, `--radius-md`, padding `--space-4`. No shadow. Do not nest cards. |
| `Dropzone` | Dashed `--border-strong` box, `--radius-md`. Text per the spec's copy table (Spanish). Click and keyboard (Enter/Space) open the native file input. Drag-over state uses the `--accent-soft` fill. Shows the chosen file name and size with a remove button. It validates type and size client-side before upload, while the server stays authoritative. |
| `Message` | User question: right-aligned, `--accent-soft` fill, `--radius-md`, max 85% width. Answer: left, no fill, full width, plain text with preserved line breaks. Render as text, never `dangerouslySetInnerHTML`. |
| `Sources` | Under each answer, a collapsible "Fuentes (n)" (`<details>`). Each source shows its page ("Página N", from 0-based `pagina` + 1, omitted when absent) in `--mono --text-xs`, plus an excerpt clamped to 3 lines with a "Ver más" toggle. `/ask` sources carry no score: show none. An empty list (always for `rerank`) gets a one-line note instead of the `<details>`. |
| `StatusDot` | 8 px dot plus a text label ("Servidor en línea" / "Servidor sin conexión" / "Comprobando…"). Colour never stands alone. |
| `Alert` | Inline, `--*-soft` background, 1 px status-colour border-left of 3 px, icon plus a one-sentence message, and an action ("Reintentar") when one exists. Errors go in `role="alert"`, success in `role="status"`. |
| `Spinner` / `Skeleton` | Spinner inside buttons and for short waits; skeleton lines for the answer area while `/ask` runs. Never a full-page blocking overlay. |
| `EmptyState` | One sentence plus the next action (copy per the spec). Use no illustration. |

## States and feedback

- **Loading:** disable only the control that started the request. Keep the
  user's input visible. If a request may take seconds (ingestion, rerank),
  say so: "Indexing… large PDFs can take a minute."
- **Success:** confirm inline with what happened and what's next (e.g.
  "Indexado *Título*. Haz una pregunta →"). Ingest returns no chunk count, and a
  re-upload of an existing title is a 200 `updated` ("ya estaba indexado"), not
  a 409. No toasts that vanish before they are read.
- **Error:** say what failed in plain words, what the user can do, and offer
  Reintentar. Map HTTP status to fixed copy (exact strings in the spec): 400/422
  means fix the input (highlight the field, never echo the backend's English
  `detail`), 404 means document not found, 413 means file too large, 504 and
  client timeout mean the server took too long, other 5xx and network errors
  mean the server couldn't answer. Never show raw JSON or a stack trace. Log the
  detail to `console.error`.
- **Timeouts:** every request has one (`AbortController`). A timeout is an
  error state with Reintentar.

## Accessibility (non-negotiable)

- Semantic HTML first: `<header>`, `<nav>`, `<main>`, `<form>`, `<button>`,
  `<label>`. ARIA only where HTML has no equivalent.
- Every control is reachable and usable by keyboard in a logical order. In the
  composer, Enter submits and Shift+Enter adds a newline.
- After an answer arrives, announce it through an `aria-live="polite"` region.
  Do not steal focus from the composer.
- Contrast per the token table. Touch targets are ≥ 44 × 44 px on
  `(pointer: coarse)`.
- Test at 200% zoom and at 360 px width: nothing clipped and no horizontal
  scroll.

## Copy

- The UI language is **Spanish** (`<html lang="es">`), with correct accents.
  Code identifiers, file names and URL hashes stay English. Use sentence case and
  keep it short and active ("Subir PDF", "Preguntar"), not "Enviar" or "Procesar
  solicitud".
- Name things as the user sees them: "documento", "pregunta", "respuesta",
  "fuentes". Avoid "chunk", "embedding", "vector".

## Review checklist

Run this before reporting a frontend task done. Report each item as checked or
not.

- [ ] Only tokens: no raw hex, px font sizes or ad-hoc spacing in components.
- [ ] One primary button per view.
- [ ] Idle, loading, success and error designed for every request, and each
      error has a recovery path.
- [ ] Works at 360, 768 and 1280 px with no horizontal scroll, checked in a
      real browser (Playwright screenshot or manual); say which.
- [ ] Light and dark both readable.
- [ ] Keyboard-only pass: tab order, visible focus, Enter submits.
- [ ] No new runtime dependency beyond React, unless the spec allows it.
