-- Afinidad de cada resultado con cada carrera:
--   interés   = suma(peso * puntuación) / suma(peso)  sobre dimensiones de interés válidas
--   habilidad = suma(peso * puntuación) / suma(peso)  sobre dimensiones de habilidad válidas
-- Una sección sin dimensiones válidas queda en NULL (no se convierte en 0).
-- "* 1.0" evita la división entera cuando la base devuelve enteros (p. ej. SQLite).
CREATE VIEW v_career_affinity AS
SELECT
    s.result_id     AS result_id,
    w.program_id    AS program_id,
    w.program_name  AS program_name,
    w.program_type  AS program_type,
    w.category      AS category,
    SUM(CASE WHEN w.kind = 'INTEREST' THEN w.weight * s.score END) * 1.0
        / NULLIF(SUM(CASE WHEN w.kind = 'INTEREST' THEN w.weight END), 0) AS interest_affinity,
    SUM(CASE WHEN w.kind = 'SKILL' THEN w.weight * s.score END) * 1.0
        / NULLIF(SUM(CASE WHEN w.kind = 'SKILL' THEN w.weight END), 0)    AS skill_affinity
FROM v_career_weights w
JOIN v_result_scores s
  ON s.dimension_code = w.dimension_code
 AND s.is_valid
GROUP BY s.result_id, w.program_id, w.program_name, w.program_type, w.category