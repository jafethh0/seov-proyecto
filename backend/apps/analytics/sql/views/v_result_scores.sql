-- Puntuación de cada dimensión en cada evaluación enviada (sin datos personales).
CREATE VIEW v_result_scores AS
SELECT
    s.id            AS score_id,
    r.id            AS result_id,
    e.id            AS evaluation_id,
    e.submitted_at  AS submitted_at,
    d.code          AS dimension_code,
    d.name          AS dimension_name,
    d.kind          AS kind,
    s.score         AS score,
    s.level         AS level,
    s.is_valid      AS is_valid,
    s.answered      AS answered,
    s.total         AS total
FROM evaluations_resultdimensionscore s
JOIN evaluations_evaluationresult r ON r.id = s.result_id
JOIN evaluations_evaluation       e ON e.id = r.evaluation_id
JOIN questionnaires_dimension     d ON d.id = s.dimension_id