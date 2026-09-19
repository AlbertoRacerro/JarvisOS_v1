# Exact file-coverage BFS checkpoint — 2026-09-17

Baseline remains remote master `240d5e0b27d9837d40f47bddfa24871ae7a2a4bb`, root tree `26db144c1d54e4b9dd4a9ebd9ef32829bbba99ed`.

This is a durable mechanical-enumeration checkpoint for issue #656 / PR #657. It does not itself credit any file as READ and does not assert a denominator before the traversal is complete.

New exact non-recursive results in this checkpoint:

- `backend/app/api` tree `ec580ba4d7177bc6f4eeab686321e37ec1d3a4e6`: terminal complete, `truncated:false`, exactly 4 blobs: `__init__.py`, `dev_message_route.py`, `health.py`, `system.py`.
- `backend/app/core` tree `11e938416a01b4e608c375fc436e53920bce0a96`: GitHub reports `truncated:false` and no child tree is visible in the returned tree; connector display is line-truncated, so its complete immediate blob path set is not yet credited to the normalized denominator.
- `backend/app/schemas` tree `f0e412397c67dda9ecfe27b6b6cd610776eb4c5a`: terminal complete, `truncated:false`, exactly 2 blobs: `__init__.py`, `common.py`.
- `frontend/public` tree `278c79dffe00104511969635ba02454ebad1f90d`: complete, `truncated:false`, zero immediate blobs and one child tree `fonts` at SHA `d93f4f6184f7a7b2a0c3d5811f9527ea4983550a`; queue that child.
- `frontend/tests` tree `15747481e17a349b68a8b1e6efe098c7fc4c9d7d`: terminal complete, `truncated:false`, exactly 15 blobs.
- `tests/fixtures` tree `7431123ed0af068136cef1ccc2534b39257358fb`: complete, `truncated:false`, exactly 2 immediate blobs plus child trees `router_policy` (`201de4025e658b987bb356a3196e66aac282e596`) and `routing_benchmarks` (`9db26f92e523b98b81ea38f351da278935b2716f`); queue both children.
- `scripts/data_root_recovery` tree `0afa149242e66a78a4db0a2090353d56ba956208`: terminal complete, `truncated:false`, exactly 5 blobs: `__init__.py`, `cli.py`, `common.py`, `restore.py`, `snapshot.py`.

Queue delta:

- remove completed `backend/app/api`, `backend/app/schemas`, `frontend/public`, `frontend/tests`, `tests/fixtures`, and `scripts/data_root_recovery`;
- add `frontend/public/fonts` `d93f4f6184f7a7b2a0c3d5811f9527ea4983550a`;
- add `tests/fixtures/router_policy` `201de4025e658b987bb356a3196e66aac282e596`;
- add `tests/fixtures/routing_benchmarks` `9db26f92e523b98b81ea38f351da278935b2716f`;
- retain `backend/app/core` as exact-path-set unresolved because connector display truncated its otherwise `truncated:false` terminal response;
- retain `backend/app/modules`, `frontend/src`, oversized `docs`, `scripts`, `tests`, `backend/tests`, `backend/tests/bluecad`, and all queued `reports/**` descendants.

`TOTAL_TRACKED_FILES`, coverage counters, percentages, and orphan counts remain gated. No partial or approximate denominator is asserted.