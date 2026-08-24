# Tasks: Graph Augmentation & Platform Enhancements

## Completed Tasks

- [x] 1. Create `app/services/graph_augmentation.py` with GraphAugmenter class
- [x] 2. Implement ALWAYS_INVOLVED_RULES (9 architecture invariants)
- [x] 3. Implement hub detection strategy
- [x] 4. Implement critical path chain strategy
- [x] 5. Implement cross-domain detection from graph topology
- [x] 6. Implement integration work item auto-addition (capped at 8)
- [x] 7. Wire graph augmentation into estimation_engine.py (both single + phase-wise paths)
- [x] 8. Create `app/services/cloud_cost_calculator.py`
- [x] 9. Implement Azure resource mapping (CATEGORY_RESOURCE_MAP, SYSTEM_RESOURCE_MAP)
- [x] 10. Implement deployment multiplier calculation
- [x] 11. Wire cloud cost into estimation result (infraCost field)
- [x] 12. Add distribution rules to estimation_catalog.json
- [x] 13. Implement _check_distribution() with auto-correction
- [x] 14. Implement discipline scaling (breakdown matches pointEstimate)
- [x] 15. Add systemDisciplineOverrides to catalog config
- [x] 16. Update _map_to_disciplines() to use system overrides (non-QA/DevOps)
- [x] 17. Add GET /api/estimations/jobs endpoint
- [x] 18. Add active jobs banner to dashboard HTML
- [x] 19. Implement refreshActiveJobs() with 10s polling
- [x] 20. Add _backfill_scope_and_readiness() background task
- [x] 21. Add GET /api/estimations/{id}/enrichment endpoint
- [x] 22. Add _pollEnrichment() frontend function
- [x] 23. Update enrichment to update sections in-place (no tab reset)
- [x] 24. Add pagination to dashboard table (10 rows/page)
- [x] 25. Add pagination to global audit log table
- [x] 26. Add newest-first sorting to dashboard
- [x] 27. Fix month filter (robust date parsing)
- [x] 28. Add live scenario modeling (slider → instant duration update)
- [x] 29. Add "without AI" display for cost
- [x] 30. Fix tab reset on navigation to results
- [x] 31. Add filename pills to result header
- [x] 32. Update SharePoint save to include 3 new columns (positions 22-24)
- [x] 33. Update SharePoint load with positional fallback
- [x] 34. Update monthly file header template
- [x] 35. Fix CPS system multiplier (1.1 → 1.5)
- [x] 36. Add 18 missing integration pattern costs
- [x] 37. Update AI multiplier (0.7 → 0.8 global)
- [x] 38. Add SYSTEM_NAME_ALIASES for vehicles (iQube, Apache, etc.)
- [x] 39. Add _CLOUD_HINT_ handling for Azure service terms
- [x] 40. Exclude polling endpoints from rate limiter
- [x] 41. Increase frontend poll timeout to 15 minutes
- [x] 42. Fix Dockerfile to include config/ directory
- [x] 43. Update .gitignore to exclude all .env.* files
- [x] 44. Fix BRD readiness display when BRD not uploaded
- [x] 45. Generate draw.io export of system dependency graph

## Pending / Next Session

- [ ] Confidence threshold tuning (relax for well-documented PRDs)
- [ ] Scope coverage backfill to SharePoint (cell-level update)
- [ ] Admin panel hot-swap model name (runtime model change)
- [ ] PRD readiness accuracy improvement (section matching)
