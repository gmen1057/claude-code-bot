"""
Session management service
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict

from bot.config import logger, DEFAULT_WORKING_DIR
from bot.database.pool import execute_query, execute_one, get_cursor


@dataclass
class Session:
    """User session data"""
    user_id: int
    conversation_id: str = ""
    context: List[Dict] = field(default_factory=list)
    context_summary: str = ""
    working_dir: str = DEFAULT_WORKING_DIR
    active_project: str = ""
    important_decisions: List[Dict] = field(default_factory=list)
    created_at: datetime = None
    last_activity: datetime = None
    message_count: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'conversation_id': str(self.conversation_id),
            'context': self.context,
            'context_summary': self.context_summary,
            'working_dir': self.working_dir,
            'active_project': self.active_project,
            'important_decisions': self.important_decisions,
            'created_at': self.created_at,
            'last_activity': self.last_activity,
            'message_count': self.message_count
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        """Create from dictionary"""
        return cls(
            user_id=data['user_id'],
            conversation_id=str(data.get('conversation_id', '')),
            context=data.get('context', []) or [],
            context_summary=data.get('context_summary', '') or '',
            working_dir=data.get('working_dir', DEFAULT_WORKING_DIR),
            active_project=data.get('active_project', '') or '',
            important_decisions=data.get('important_decisions', []) or [],
            created_at=data.get('created_at'),
            last_activity=data.get('last_activity'),
            message_count=data.get('message_count', 0)
        )


class SessionManager:
    """Manages user sessions with database persistence"""

    def __init__(self):
        # In-memory cache for fast access
        self._cache: Dict[int, Session] = {}

    def get_session(self, user_id: int) -> Session:
        """Get or create a session for user"""
        # Check cache first
        if user_id in self._cache:
            return self._cache[user_id]

        # Try to load from database
        row = execute_one(
            "SELECT * FROM sessions WHERE user_id = %s",
            (user_id,)
        )

        if row:
            session = Session.from_dict(dict(row))
            self._cache[user_id] = session
            logger.info(f"Session loaded for user {user_id}")
            return session

        # Create new session
        execute_one(
            "INSERT INTO sessions (user_id) VALUES (%s) RETURNING *",
            (user_id,)
        )

        row = execute_one(
            "SELECT * FROM sessions WHERE user_id = %s",
            (user_id,)
        )

        session = Session.from_dict(dict(row))
        self._cache[user_id] = session
        logger.info(f"New session created for user {user_id}")
        return session

    def update_session(self, user_id: int, **updates) -> None:
        """Update session fields"""
        # Update cache
        if user_id in self._cache:
            session = self._cache[user_id]
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)

        # Update database
        set_parts = []
        values = []

        for key, value in updates.items():
            if key in ('context', 'important_decisions'):
                set_parts.append(f"{key} = %s::jsonb")
                values.append(json.dumps(value) if isinstance(value, (list, dict)) else value)
            else:
                set_parts.append(f"{key} = %s")
                values.append(value)

        if not set_parts:
            return

        set_parts.append("last_activity = CURRENT_TIMESTAMP")
        values.append(user_id)

        query = f"UPDATE sessions SET {', '.join(set_parts)} WHERE user_id = %s"

        with get_cursor() as cur:
            cur.execute(query, values)

    def add_message(self, user_id: int, user_msg: str, assistant_msg: str, source: str = 'telegram') -> None:
        """Add a message to session context"""
        session = self.get_session(user_id)

        message = {
            'user': user_msg,
            'assistant': assistant_msg,
            'timestamp': datetime.now().isoformat(),
            'source': source
        }

        session.context.append(message)
        session.message_count += 1

        self.update_session(
            user_id,
            context=session.context,
            message_count=session.message_count
        )

    def reset_session(self, user_id: int) -> Session:
        """Reset session to initial state"""
        # Remove from cache
        if user_id in self._cache:
            del self._cache[user_id]

        # Delete and recreate in database
        with get_cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
            cur.execute("INSERT INTO sessions (user_id) VALUES (%s)", (user_id,))

        logger.info(f"Session reset for user {user_id}")
        return self.get_session(user_id)

    def clear_cache(self) -> None:
        """Clear in-memory cache"""
        self._cache.clear()


def log_command(user_id: int, command: str, response: str, execution_time_ms: int = None, error: str = None) -> None:
    """Log a command execution"""
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO command_logs (user_id, command, response, execution_time_ms, error)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, command[:2000], response[:5000] if response else None, execution_time_ms, error))


def get_command_history(user_id: int, limit: int = 20) -> List[Dict]:
    """Get command history for user"""
    with get_cursor(dict_cursor=True) as cur:
        cur.execute("""
            SELECT command, response, execution_time_ms, error, created_at
            FROM command_logs
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))
        return cur.fetchall()


# Global session manager instance
session_manager = SessionManager()
