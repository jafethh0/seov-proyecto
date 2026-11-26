-- Resumen general (solo conteos, sin datos personales).
SELECT
    (SELECT COUNT(*) FROM evaluations_evaluation WHERE status = 'SUBMITTED')            AS submitted_evaluations,
    (SELECT COUNT(*) FROM evaluations_evaluation WHERE status = 'DRAFT')                AS drafts,
    (SELECT COUNT(DISTINCT user_id) FROM evaluations_evaluation WHERE status = 'SUBMITTED') AS students_with_results,
    (SELECT COUNT(*) FROM catalog_careerprogram WHERE is_active)                        AS active_careers,
    (SELECT COUNT(*) FROM v_available_offerings)                                        AS available_offerings