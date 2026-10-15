# Personal Operations / Aurelius Integration — Feasibility Note

Discovery only, 2026-10-15. No personal software implementation or academic data import is authorized here. The founder first establishes the real timetable, protects sleep and study time, tests a manual routine, and observes friction for roughly one to two weeks.

| Classification | Current evidence and decision |
| --- | --- |
| **AVAILABLE NOW** | Spec 116's Development owner has workspace-scoped Roadmap work items, dependencies, lifecycle/completion, revision checks, and linked Calendar allocations with time zones (`backend/app/modules/development/{models,routes,service}.py`, `backend/app/core/development_schema.py`). `frontend/src/pages/DevelopmentRoadmap.tsx` has Timeline and Day/Week/Month/Agenda views. These are engineering-project facilities. |
| **CONFIGURATION ONLY** | A manual study routine can be tested in a current personal tool, with realistic timetable, sleep boundary and study priorities entered by the founder. This does not require JarvisOS changes. |
| **INTEGRATION GAP** | No accessible current Aurelius repository, API, task schema, time-block schema or completion contract was found in the bounded local audit. Its historical planning use is context, not implementation proof. The Development API is stable for its own domain; it is not a personal task interface. |
| **FUTURE FEATURE** | A personal data owner would still need explicit completion records, active-study timers/stopwatches, recurring routines, review workflow and configurable reminders. The existing Calendar `reminder` is stored metadata, not evidence of notification delivery. No shipped mobile app, push worker or personal time-tracking service was found. |
| **NOT RECOMMENDED** | Putting coursework/sleep data into Development tables, maintaining two writable calendar/task truths, importing personal data before a source-of-truth decision, or autonomous AI rescheduling of study commitments. |

The Development calendar's components, IANA time-zone handling and revision patterns could be reused at the UI or implementation-pattern level after a personal owner is designed. Current interfaces do not establish a safe cross-domain task/time/completion contract. An iPhone notification path would require a reachable secure web app or native app, device permission, and a push-delivery/service-worker or native notification channel; mobile browser access alone does not deliver reminders.

Keep timetable, study progress, sleep/routine data, private commitments and supervision details local and under explicit user control. If Aurelius later proves to be the canonical personal planner, the smallest authorized increment would be a read-only, identity-preserving view of its verified task/time data in JarvisOS. Any write/sync direction needs a separate explicit design and conflict policy. The need for timers, recurrence, reviews and notification frequency should be judged from the observed routine rather than assumed now.

Evidence limit: this note inspected repository code and bounded local project directories; it did not access Aurelius source. It makes no claim that Aurelius lacks a feature or an API, only that neither was verified here.
