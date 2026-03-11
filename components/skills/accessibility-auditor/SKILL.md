---
name: accessibility-auditor
description: WCAG 2.1 AA/AAA compliance audit with color contrast, keyboard navigation, ARIA, and screen reader checks.
requires:
  bins:
    - npx  # for axe, pa11y, lighthouse
install: "npm install -g axe-cli pa11y lighthouse"
# Context cost: ~80 lines (~1.5K tokens)
---

# Accessibility Auditor Skill

## Trigger
Activated when asked about accessibility, a11y, WCAG, screen readers, or inclusive design.

## Capabilities
- WCAG 2.1 AA/AAA compliance checking
- Screen reader compatibility analysis
- Keyboard navigation audit
- Color contrast verification
- ARIA implementation review
- Focus management analysis
- Semantic HTML validation

## WCAG Checklist

### Perceivable
- [ ] Alt text for images
- [ ] Captions for video/audio
- [ ] Color contrast (4.5:1 normal, 3:1 large text)
- [ ] Text resizable to 200%
- [ ] No content conveyed by color alone

### Operable
- [ ] All functionality via keyboard
- [ ] No keyboard traps
- [ ] Skip navigation links
- [ ] Focus visible indicators
- [ ] No seizure-inducing content
- [ ] Touch targets ≥44x44px

### Understandable
- [ ] Language declared
- [ ] Consistent navigation
- [ ] Error identification and suggestions
- [ ] Labels for form inputs

### Robust
- [ ] Valid HTML
- [ ] ARIA used correctly
- [ ] Name, role, value exposed
- [ ] Status messages announced

## Testing Commands
```bash
# Automated testing
npx axe <url>
npx pa11y <url>
lighthouse <url> --only-categories=accessibility

# Color contrast
# Use: https://webaim.org/resources/contrastchecker/
```

## Output Format
```
ACCESSIBILITY AUDIT
===================
WCAG Level: [A/AA/AAA]
Score: [0-100]
Issues Found: [count]

CRITICAL (blocks users)
-----------------------
1. [Issue] - WCAG [criterion]
   Element: <selector>
   Problem: [description]
   Fix: [code example]

SERIOUS (significant barrier)
-----------------------------
...

MODERATE (some difficulty)
--------------------------
...

RECOMMENDATIONS
---------------
- [Priority improvements]
```
