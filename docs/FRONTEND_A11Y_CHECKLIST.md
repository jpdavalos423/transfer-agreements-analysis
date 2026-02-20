# Frontend Accessibility and Mobile Checklist

Scope: `apps/frontend` React + Vite UI.

## Automated Baseline Check

Run from repo root:

```bash
cd apps/frontend
npm run a11y:check
```

What it verifies:
- Focus-visible CSS exists
- Skip-link CSS exists
- Skip links exist on setup/pathway pages
- Setup form controls are labeled
- Multi-select has assistive help text wiring
- Mobile media query exists

## Manual QA Checklist

Run API + frontend, then verify:

1. Keyboard navigation:
- Use only `Tab`/`Shift+Tab` to reach all controls on `/` and `/pathway`.
- Activate actions with keyboard (`Enter`/`Space`) for submit/retry.

2. Skip links:
- On `/`, tab once and confirm "Skip to planner setup form" appears and works.
- On `/pathway`, tab once and confirm "Skip to pathway content" appears and works.

3. Labels and instructions:
- Each setup field has a visible label.
- Target UCs multi-select includes helper text and remains readable.

4. Focus visibility:
- Focus ring is visible for links, inputs, selects, textarea, buttons.

5. Error/status announcements:
- Trigger validation errors and confirm they render in the error panel.
- Trigger request error and confirm code/message/details are readable.

6. Mobile responsiveness:
- Simulate narrow viewport (e.g., 390px width).
- No horizontal page scrolling.
- Results/status stack vertically.
- Retry/back controls remain tappable.

## Notes

This checklist is a baseline. It does not replace a full WCAG audit.
