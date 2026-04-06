"""
Миграция 005: Таблица subscribe_tasks
"""

MIGRATION_ID = "005"
DESCRIPTION = "Добавить таблицу subscribe_tasks для предподготовки кампаний"

UP_SQL = [
    """
    CREATE TABLE IF NOT EXISTS subscribe_tasks (
        id            SERIAL PRIMARY KEY,
        user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        account_ids   JSONB DEFAULT '[]',
        channels      JSONB DEFAULT '[]',
        total_minutes INTEGER DEFAULT 240,
        status        VARCHAR(32) DEFAULT 'pending',
        progress      INTEGER DEFAULT 0,
        subscribed    INTEGER DEFAULT 0,
        failed        INTEGER DEFAULT 0,
        skipped       INTEGER DEFAULT 0,
        error         TEXT,
        results       JSONB DEFAULT '[]',
        started_at    TIMESTAMP,
        finished_at   TIMESTAMP,
        created_at    TIMESTAMP DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_subscribe_tasks_user_id ON subscribe_tasks(user_id)",
]

DOWN_SQL = [
    "DROP TABLE IF EXISTS subscribe_tasks",
]
