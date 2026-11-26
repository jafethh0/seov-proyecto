-- Carreras más recomendadas (veces recomendada, veces en el top 3 y compatibilidad media).
SELECT
    p.id                                        AS program_id,
    p.name                                      AS name,
    c.name                                      AS category,
    COUNT(*)                                    AS times_recommended,
    SUM(CASE WHEN r.rank <= 3 THEN 1 ELSE 0 END) AS times_top3,
    ROUND(AVG(r.compat), 2)                     AS avg_compat
FROM evaluations_careerrecommendation r
JOIN catalog_careerprogram  p ON p.id = r.program_id
JOIN catalog_careercategory c ON c.id = p.category_id
GROUP BY p.id, p.name, c.name
ORDER BY times_top3 DESC, times_recommended DESC, p.name ASC
LIMIT %(limit)s