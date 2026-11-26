-- Por dimensión: cuántas evaluaciones la tienen válida, promedio y reparto por nivel.
SELECT
    dimension_code,
    dimension_name,
    kind,
    COUNT(*)                                            AS evaluations,
    SUM(CASE WHEN is_valid THEN 1 ELSE 0 END)           AS valid_count,
    ROUND(AVG(score), 2)                                AS avg_score,
    SUM(CASE WHEN level = 'HIGH'   THEN 1 ELSE 0 END)   AS high_count,
    SUM(CASE WHEN level = 'MEDIUM' THEN 1 ELSE 0 END)   AS medium_count,
    SUM(CASE WHEN level = 'LOW'    THEN 1 ELSE 0 END)   AS low_count
FROM v_result_scores
GROUP BY dimension_code, dimension_name, kind
ORDER BY kind, dimension_code