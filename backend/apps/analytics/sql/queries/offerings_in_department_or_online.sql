-- Ofertas disponibles en un departamento, más las en línea (se cursan desde cualquier lugar).
SELECT * FROM v_available_offerings
WHERE department_id = %(department_id)s OR modality = 'ONLINE'
ORDER BY program_name, institution, campus