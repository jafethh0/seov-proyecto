-- Cobertura del catálogo: ofertas disponibles y carreras distintas por departamento.
SELECT
    d.id    AS department_id,
    d.name  AS department,
    d.slug  AS slug,
    COUNT(v.offering_id)           AS offerings,
    COUNT(DISTINCT v.program_id)   AS programs
FROM catalog_department d
LEFT JOIN v_available_offerings v ON v.department_id = d.id
GROUP BY d.id, d.name, d.slug
ORDER BY d.name