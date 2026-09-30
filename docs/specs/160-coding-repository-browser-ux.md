# 160 — Coding repository browser UX

State: **ready contract, implementation active** under the 2026-09-30 maintainer directive. Dependencies 118 and 140 are merged. This is a bounded frontend usability change to the existing `/coding/repository` surface and its tests. The accepted 118/140 backend and Coding read/action contracts remain authoritative.

## Outcome

An operator can browse the configured repository with a single dominant central viewport. At a directory, the viewport shows only that directory's folders and files as a clean list or table with recognizable folder/file affordances, names, and useful metadata already returned by the backend. Selecting a folder navigates into it. A breadcrumb names the repository and each path segment, and offers direct ancestor navigation plus a clear parent/back action.

Selecting a file replaces the directory listing in the same viewport with a readable file preview. The file view has an obvious action back to its containing directory. A full nested tree is not displayed beside the file. Browser Back/Forward should restore directory/file navigation where practical without changing repository authority or exposing a second state store.

Repository identity, requested ref, and resolved exact SHA remain available as truthful secondary information. Literal search stays available as a secondary tool. Jarvis Sidecar may remain on the right. The existing PR evidence, inspect, explicit context and proposal capabilities remain reachable without competing with the browse/read path.

## Boundaries

- Reuse `CodingWorkbench`, `frontend/src/api/coding.ts`, and the existing server-owned `/api/coding/repository/*` projections. Do not create another repository owner, mirror, cache, store, GitHub client, or filesystem capability.
- Ordinary directory navigation, file preview, search and PR reading are read-only and context-neutral. `Add to Jarvis context` remains an explicit action, preserving exact repository/ref/SHA/path and 111/123 context binding. No browser GitHub credentials, mutation, commit, push, PR creation, merge, execution or Development action authority.
- Preserve 118/140 exact repository/ref/SHA semantics, safe server-provided GitHub URLs, bounded preview, and truthful partial, refused, loading, empty and stale/error states. The UI must never present an old directory/file response as current after navigation or ref refresh.
- Preserve the existing `/coding/runtime` behavior. Visual changes are local to the repository route and do not redesign the app shell or Sidecar.
- Use familiar repository-browser spacing, readable rows, breadcrumb, and file-preview conventions without copying GitHub branding.

## Acceptance

1. At desktop width, the current directory list is the dominant center surface. Folders precede or are clearly distinguishable from files; clicking a folder shows its contents and an accurate breadcrumb. Parent and ancestor navigation work.
2. Clicking a file gives a single central viewer for that file; no full directory tree remains beside it. The viewer has a clear return to the containing directory and readable text/Markdown presentation.
3. Browser Back/Forward restores the current directory or file when feasible, including a direct file opened from search. Reload preserves a valid route state or returns clearly to root; it never invents a path or SHA.
4. Repository/ref/SHA information and literal search are visible but secondary. Existing metadata is shown only when actually returned; no fabricated commit age, author, or file data.
5. Loading, empty, partial, unsupported/binary and failure states remain explicit in the relevant viewport. Stale asynchronous responses cannot replace a newer navigation target.
6. Browsing and previewing make only existing JarvisOS read requests and do not add Jarvis context. Explicit `Add to Jarvis context` remains separately actionable; existing inspect/proposal boundaries and error handling remain intact.
7. At desktop and compact-desktop widths (nominally 1440 and 1024 CSS pixels), the directory, breadcrumb, viewer and return controls remain usable without the prior nested-tree-plus-file split.

## Evidence

- Deterministic frontend checks for retained 118/140 API and context boundaries and the new navigation/layout contract; frontend production build.
- Exact-final-head real-browser acceptance against the existing backend at desktop and compact-desktop widths, including directory→folder→file→back, browser history, visible exact SHA/partial state, explicit context boundary, and screenshots inspected for layout/readability.
- Exact-head CI green, severe semantic diff inspection, truthful STATUS/PR linkage, merge, fresh-master verification, canonical deployment and `/coding/repository` smoke.
