-- Ofertas que se pueden mostrar al estudiante: activas, con fuente y fecha de verificación,
-- no desactualizadas, y con sede, institución y carrera activas.
-- Es la versión declarativa (SQL) de ProgramOffering.objects.available().
CREATE VIEW v_available_offerings AS
SELECT
    o.id                      AS offering_id,
    o.program_id              AS program_id,
    p.name                    AS program_name,
    p.program_type            AS program_type,
    c.name                    AS category,
    i.id                      AS institution_id,
    i.name                    AS institution,
    i.acronym                 AS acronym,
    i.sector                  AS sector,
    ca.id                     AS campus_id,
    ca.name                   AS campus,
    ca.city                   AS city,
    d.id                      AS department_id,
    d.slug                    AS department_slug,
    d.name                    AS department,
    o.official_name           AS official_name,
    o.modality                AS modality,
    o.duration_months         AS duration_months,
    o.admission_requirements  AS admission_requirements,
    o.source_url              AS source_url,
    o.verified_at             AS verified_at
FROM catalog_programoffering o
JOIN catalog_careerprogram  p  ON p.id  = o.program_id
JOIN catalog_careercategory c  ON c.id  = p.category_id
JOIN catalog_campus         ca ON ca.id = o.campus_id
JOIN catalog_institution    i  ON i.id  = ca.institution_id
JOIN catalog_department     d  ON d.id  = ca.department_id
WHERE o.is_active
  AND o.verified_at IS NOT NULL
  AND o.source_url <> ''
  AND o.verification_status <> 'OUTDATED'
  AND ca.is_active
  AND i.is_active
  AND p.is_active