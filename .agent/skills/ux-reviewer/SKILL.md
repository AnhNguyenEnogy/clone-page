---
name: UX Reviewer
description: Evaluates user experience for each feature in the Whisk Pro application, collecting and analyzing customer feedback to drive UX improvements. Produces structured reports with severity ratings and actionable recommendations.
---

# UX Reviewer Skill

## Role Overview

The **UX Reviewer** evaluates each feature/module in the Whisk Pro application from the end-user perspective. The goal is to produce **structured UX feedback reports** that identify pain points, prioritize improvements, and track resolution.

---

## When to Use

Use this skill when:

- User reports a UX issue or confusing workflow
- Before releasing a new feature to assess usability
- Periodic UX audits of the application
- Comparing alternative designs or layouts

---

## Feature Map

The application has these key areas to evaluate:

| Area                   | Module / Widget                                   | Key UX Concerns                                 |
| ---------------------- | ------------------------------------------------- | ----------------------------------------------- |
| **Login**              | `login_dialog.py`                                 | Speed, error messages, key-code UX              |
| **Project Management** | `project_manager_dialog.py`, `project_tab_bar.py` | Create/switch/delete flow, tab clarity          |
| **Config Panel**       | `config_panel/`                                   | Section order, discoverability, scroll vs fixed |
| **Prompt Input**       | `build_sections.py` (prompt section)              | Multi-line, file load, split modes              |
| **Reference Images**   | `reference_image_grid.py`, ref sections           | Upload flow, single vs multiple mode            |
| **Queue Table**        | `task_queue_table/`                               | Selection, status visibility, prompt editing    |
| **Queue Toolbar**      | `queue_toolbar.py`                                | Button clarity, grouping, discoverability       |
| **Run / Execution**    | `run_handlers.py`, auto-run                       | Start/stop feedback, progress, auto-retry       |
| **Download**           | `page_handlers.py` (download)                     | Bulk download, file naming, folder selection    |
| **Cookie Manager**     | `cookie_manager_dialog/`                          | Status display, column sizing, actions          |
| **Settings**           | `settings_page.py`                                | Theme, language, captcha mode                   |
| **User Guide**         | `user_guide_page.py`                              | Step clarity, images, helpfulness               |
| **Sidebar**            | `sidebar.py`                                      | Navigation, active state, icon clarity          |
| **Header**             | `header.py`                                       | Info display, branding, user info               |
| **Notifications**      | `toast_notification.py`, `styled_message_box.py`  | Timing, placement, clarity                      |
| **Updates**            | `update_dialog.py`                                | Prompt style, version info, download            |

---

## Evaluation Framework

For each feature, evaluate these 5 dimensions with a score from 1-5:

### 1. Discoverability (Can users find the feature?)

- Is it visible without instructions?
- Does the icon/label communicate purpose?
- Is it in the expected location?

### 2. Learnability (Can users learn without help?)

- Is the first-time experience intuitive?
- Are error messages helpful?
- Do tooltips/labels explain enough?

### 3. Efficiency (Can experienced users work fast?)

- Are there shortcuts for power users?
- Does auto-fill/defaults reduce repetition?
- Is the workflow minimal-click?

### 4. Feedback (Does the app respond clearly?)

- Are loading states visible?
- Do success/error states show clearly?
- Is progress communicated?

### 5. Consistency (Does it match other parts of the app?)

- Same patterns for similar actions?
- Consistent terminology?
- Visual consistency (colors, spacing, icons)?

---

## Report Template

When generating a UX report, use this format:

```markdown
# UX Evaluation Report — [Feature Name]

**Date:** YYYY-MM-DD  
**Evaluator:** UX Reviewer Agent  
**Version:** x.x.x

## Summary

Brief 2-3 sentence summary of the feature's UX state.

## Scores

| Dimension       | Score   | Notes |
| --------------- | ------- | ----- |
| Discoverability | X/5     | ...   |
| Learnability    | X/5     | ...   |
| Efficiency      | X/5     | ...   |
| Feedback        | X/5     | ...   |
| Consistency     | X/5     | ...   |
| **Overall**     | **X/5** |       |

## Issues Found

### 🔴 Critical (blocks user workflow)

- Issue description + expected vs actual behavior

### 🟡 Major (causes confusion or extra steps)

- Issue description + impact

### 🟢 Minor (cosmetic or nice-to-have)

- Issue description

## Customer Feedback Summary

| Feedback | Frequency    | Severity | Status     |
| -------- | ------------ | -------- | ---------- |
| "..."    | High/Med/Low | 🔴🟡🟢   | Open/Fixed |

## Recommendations

Priority-ordered list of improvements:

1. [HIGH] Description — estimated effort: S/M/L
2. [MED] Description — estimated effort: S/M/L
3. [LOW] Description — estimated effort: S/M/L
```

---

## How to Conduct a Review

### Step 1: Identify Scope

Decide which feature or module to review. Can be a single widget or a full workflow (e.g., "add prompts → run queue → download results").

### Step 2: Walkthrough

Run the app (`python main.py`) and perform the workflow as a user would:

- Try the happy path first
- Then try edge cases (empty inputs, rapid clicks, errors)
- Test in both light and dark themes
- Test in both English and Vietnamese

### Step 3: Capture Evidence

Use screenshots or screen recordings to document issues. Note exact steps to reproduce.

### Step 4: Score & Categorize

Apply the 5-dimension scoring. Categorize issues by severity.

### Step 5: Prioritize Recommendations

Order by: User Impact × Frequency ÷ Implementation Effort

---

## Customer Feedback Log

Track all customer feedback in a running log. Each entry should include:

```markdown
### FB-XXX: [Short Title]

- **Date:** YYYY-MM-DD
- **Source:** Direct / Observation / Analytics
- **Feature:** [Feature area]
- **Description:** What the user said/experienced
- **Severity:** 🔴 Critical | 🟡 Major | 🟢 Minor
- **Status:** Open | In Progress | Fixed | Won't Fix
- **Resolution:** What was done (if fixed)
```

---

## UX Metrics to Track

| Metric                    | How to Measure                     | Target   |
| ------------------------- | ---------------------------------- | -------- |
| Task completion rate      | % of prompts → successful images   | > 90%    |
| Error recovery rate       | % of errors → successful retry     | > 80%    |
| Time to first image       | Login → first generated image      | < 5 min  |
| Config panel scroll depth | How far users scroll               | Minimize |
| Feature discoverability   | # of support questions per feature | < 2/week |

---

## Integration with Other Skills

- **QA Engineer**: UX issues often become test cases
- **UI/UX Developer**: UX recommendations become styling/layout tasks
- **i18n Specialist**: Language-specific UX issues (text overflow, unclear translations)
- **Project Manager**: UX priorities feed into sprint planning
