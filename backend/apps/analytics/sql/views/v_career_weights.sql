-- Peso de cada dimensión (interés o habilidad) en cada carrera activa.
CREATE VIEW v_career_weights AS
SELECT
    p.id            AS program_id,
    p.name          AS program_name,
    p.program_type  AS program_type,
    c.name          AS category,
    d.code          AS dimension_code,
    d.kind          AS kind,
    cd.weight       AS weight
FROM catalog_careerdimension cd
JOIN catalog_careerprogram   p ON p.id = cd.program_id
JOIN catalog_careercategory  c ON c.id = p.category_id
JOIN questionnaires_dimension d ON d.id = cd.dimension_id
WHERE p.is_active
  AND d.is_active