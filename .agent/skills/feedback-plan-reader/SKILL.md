---
name: Feedback Plan Reader
description: Reads and analyzes feedback plans from the `.feedback` directory — triages inbox, reviews responses, tracks action-plan progress, and reports summary status to the user.
---

# Feedback Plan Reader Skill

## Role Overview

The **Feedback Plan Reader** is responsible for:

- Reading and summarizing feedback from `.feedback/inbox.md`
- Reviewing response decisions in `.feedback/responses.md`
- Tracking action-plan progress in `.feedback/action-plan.md`
- Reporting status, blockers, and next steps to the user

> [!IMPORTANT]
> **Mandatory Rule**: When the user asks to read or review feedback plans (`đọc plan`, `xem feedback`, `báo cáo feedback`), you **MUST** read all 3 core files in `.feedback/` and produce a structured summary.

---

## `.feedback` Directory Structure

| File             | Purpose                                                   |
| ---------------- | --------------------------------------------------------- |
| `README.md`      | Overview of the feedback workspace and workflow           |
| `inbox.md`       | Raw feedback entries from Codex (unprocessed or triaged)  |
| `responses.md`   | Official responses sent to the antigravity team           |
| `action-plan.md` | Task tracking table with priority, owner, ETA, and status |

---

## Workflow

```
inbox.md → responses.md → action-plan.md
```

1. New feedback is logged in `inbox.md` with a `Feedback ID`.
2. Analysis and response are written in `responses.md`.
3. Actionable tasks are created in `action-plan.md`.
4. Status is updated until `Done`.

---

## How to Read Plans

### Step 1: Read Inbox

Open `.feedback/inbox.md` and list all feedback entries. For each entry, note:

- **Feedback ID** (e.g., `FB-20260305-PERF-001`)
- **Module/Area** affected
- **Severity** (High / Medium / Low)
- **Status** (New / Triaged / Planned / Done)

### Step 2: Read Responses

Open `.feedback/responses.md` and match responses to inbox entries by `Feedback ID`. For each, note:

- **Decision** (Accept / Reject / Need More Info)
- **Response summary** — what was communicated to the team
- **Owner** and **ETA**

### Step 3: Read Action Plan

Open `.feedback/action-plan.md` and scan the **Active Plan** table. For each row, note:

- **Task** description
- **Priority** (P1 / P2 / P3)
- **Status** (Todo / In Progress / Blocked / Done)
- **Owner** and **ETA**

### Step 4: Generate Summary Report

Produce a structured summary using the template below.

---

## Report Template

```markdown
# Feedback Plan Status Report

**Date:** YYYY-MM-DD
**Reader:** Feedback Plan Reader Agent

## Inbox Summary

| Feedback ID | Module/Area | Severity | Status |
| ----------- | ----------- | -------- | ------ |

## Response Summary

| Feedback ID | Decision | Owner | ETA |
| ----------- | -------- | ----- | --- |

## Action Plan Progress

| Feedback ID | Total Tasks | Done | In Progress | Todo | Blocked |
| ----------- | ----------- | ---- | ----------- | ---- | ------- |

### Overdue Tasks

List tasks where ETA < today and Status ≠ Done.

### Blocked Tasks

List tasks with Status = Blocked and explain why.

## Next Steps

Priority-ordered list of recommended actions:

1. [P1] ...
2. [P2] ...
```

---

## Identifying Issues

When reading plans, flag these situations:

| Issue                | How to Detect                            | Action                     |
| -------------------- | ---------------------------------------- | -------------------------- |
| **Orphan feedback**  | Inbox entry without matching response    | Flag as "Needs Response"   |
| **Stale task**       | ETA passed, status still Todo            | Flag as "Overdue"          |
| **Missing owner**    | Task in action-plan without @owner       | Flag as "Unassigned"       |
| **Blocked chain**    | Blocked task blocking other tasks        | Highlight dependency chain |
| **Unplanned accept** | Response = Accept but no action-plan row | Flag as "Needs Planning"   |

---

## Integration with Other Skills

- **Project Manager**: Feedback tasks feed into sprint planning and progress reports
- **UX Reviewer**: UX-related feedback entries may trigger UX evaluations
- **QA Engineer**: Performance feedback (e.g., PERF) may require benchmark test cases
- **DevOps Engineer**: Deployment-related feedback items coordinate with build/release
