-- Compatibilidad de un resultado con TODAS las carreras, calculada solo con SQL.
--   A: hay interés y habilidad  -> w_interest * I + w_skill * H
--   B: solo interés             -> I
--   C: solo habilidad           -> H
--   D: ninguno                  -> la carrera no aparece (nunca se devuelve 0)
SELECT
    program_id,
    program_name AS name,
    program_type,
    category,
    interest_affinity,
    skill_affinity,
    ROUND(CASE
        WHEN interest_affinity IS NOT NULL AND skill_affinity IS NOT NULL
            THEN %(w_interest)s * interest_affinity + %(w_skill)s * skill_affinity
        WHEN interest_affinity IS NOT NULL THEN interest_affinity
        ELSE skill_affinity
    END, 2) AS compat,
    CASE
        WHEN interest_affinity IS NOT NULL AND skill_affinity IS NOT NULL THEN 'A'
        WHEN interest_affinity IS NOT NULL THEN 'B'
        ELSE 'C'
    END AS case_code
FROM v_career_affinity
WHERE result_id = %(result_id)s
  AND (interest_affinity IS NOT NULL OR skill_affinity IS NOT NULL)
ORDER BY compat DESC, program_name ASC