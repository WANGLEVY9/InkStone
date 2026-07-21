-- Local MySQL seed snapshot for CI/CD.
-- Keep this file data-only (no CREATE TABLE statements).
-- Typical export command:
-- mysqldump -h127.0.0.1 -P3307 -uagent -pagent123 --single-transaction --skip-triggers --no-create-info agent_eval metric_definitions evaluation_strategies > deploy/sql/local_seed.sql
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
INSERT INTO metric_definitions (
        name,
        metric_type,
        logic_type,
        ragas_config,
        description
    )
VALUES (
        'response_time',
        'explicit',
        'builtin',
        JSON_OBJECT(),
        'Response latency score.'
    ),
    (
        'token_usage',
        'explicit',
        'builtin',
        JSON_OBJECT(),
        'Token consumption score.'
    ),
    (
        'tool_accuracy',
        'explicit',
        'builtin',
        JSON_OBJECT(),
        'Tool call success ratio.'
    ),
    (
        'task_success',
        'explicit',
        'builtin',
        JSON_OBJECT(),
        'Task completion score.'
    ),
    (
        'answer_relevancy',
        'fuzzy',
        'ragas',
        JSON_OBJECT('source_key', 'answer_relevancy'),
        'Answer relevancy from RAGAS output.'
    ) ON DUPLICATE KEY
UPDATE metric_type =
VALUES(metric_type),
    logic_type =
VALUES(logic_type),
    ragas_config =
VALUES(ragas_config),
    description =
VALUES(description);
INSERT INTO evaluation_strategies (name, weights, metrics, description)
VALUES (
        'balanced-default',
        JSON_OBJECT(
            'response_time',
            0.2,
            'token_usage',
            0.2,
            'tool_accuracy',
            0.25,
            'task_success',
            0.35
        ),
        JSON_ARRAY(
            'response_time',
            'token_usage',
            'tool_accuracy',
            'task_success'
        ),
        'Balanced strategy for generic online evaluation.'
    ),
    (
        'quality-first',
        JSON_OBJECT(
            'task_success',
            0.45,
            'tool_accuracy',
            0.3,
            'answer_relevancy',
            0.25
        ),
        JSON_ARRAY(
            'task_success',
            'tool_accuracy',
            'answer_relevancy'
        ),
        'Prefer quality and correctness for production gating.'
    ) ON DUPLICATE KEY
UPDATE weights =
VALUES(weights),
    metrics =
VALUES(metrics),
    description =
VALUES(description);
SET FOREIGN_KEY_CHECKS = 1;