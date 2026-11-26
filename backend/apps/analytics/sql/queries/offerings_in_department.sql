-- Ofertas disponibles en un departamento (solo presenciales y semipresenciales de ahí).
SELECT * FROM v_available_offerings
WHERE department_id = %(department_id)s
ORDER BY program_name, institution, campus