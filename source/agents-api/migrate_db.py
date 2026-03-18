import asyncio
import os
from sqlalchemy import text
from app.utils.database import engine

async def migrate():
    print("Running migration for agent_sessions enhancements...")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS current_agent VARCHAR DEFAULT 'L1 Support Specialist'"))
            await conn.execute(text("ALTER TABLE agent_sessions ADD COLUMN IF NOT EXISTS session_name TEXT"))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS a2a_context (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
                    from_agent TEXT NOT NULL,
                    to_agent TEXT NOT NULL,
                    context_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Backfill session_name from first user message for legacy sessions.
            await conn.execute(text("""
                UPDATE agent_sessions s
                SET session_name = COALESCE(
                    NULLIF(
                        SUBSTRING(
                            TRIM(REGEXP_REPLACE(m.content, '[^[:alnum:][:space:]]', '', 'g'))
                            FROM 1 FOR 20
                        ),
                        ''
                    ),
                    'Untitled Session'
                )
                FROM (
                    SELECT DISTINCT ON (session_id) session_id, content
                    FROM agent_messages
                    WHERE role = 'user' AND content IS NOT NULL AND LENGTH(TRIM(content)) > 0
                    ORDER BY session_id, id ASC
                ) m
                WHERE s.session_id = m.session_id
                  AND (s.session_name IS NULL OR LENGTH(TRIM(s.session_name)) = 0)
            """))

            # If a session still has no name (e.g., no user message), set safe default.
            await conn.execute(text("""
                UPDATE agent_sessions
                SET session_name = 'Untitled Session'
                WHERE session_name IS NULL OR LENGTH(TRIM(session_name)) = 0
            """))
            await conn.commit()
            print("Migration successful: current_agent, session_name, and a2a_context ensured.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        # Ensure asyncpg connections/transports are closed before event loop shutdown
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
