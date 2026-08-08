# -----------------------------------------------------------------
# database.py
#
# Sets up the SQLite database. SQLite stores everything in one
# local file (see SQLITE_DB_PATH in config.py) - there is no
# separate database server to install, start, or connect to over
# the network, which makes it very easy to set up for a student
# project.
#
# We use Python's built-in "sqlite3" module directly (no ORM like
# SQLAlchemy) so every SQL query in the services/ layer is plain,
# readable SQL that's easy to explain in a viva.
# -----------------------------------------------------------------

import sqlite3
from contextlib import contextmanager

from app.config import SQLITE_DB_PATH
from app.models.conversation import CREATE_CONVERSATIONS_TABLE_SQL
from app.models.message import CREATE_MESSAGES_TABLE_SQL
from app.models.student import CREATE_STUDENTS_TABLE_SQL


@contextmanager
def get_db():
    """
    Opens a SQLite connection for ONE unit of work (e.g. one API
    request), and always closes it afterwards - even if an error
    happens. Used like this:

        with get_db() as conn:
            conn.execute("INSERT INTO students (...) VALUES (...)", (...))

    `row_factory = sqlite3.Row` lets us read query results like a
    dictionary (row["name"]) instead of by numeric index (row[1]).
    """
    connection = sqlite3.connect(SQLITE_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")  # enforce student_id/conversation_id links
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db():
    """Creates all tables (if they don't already exist). Called once when the app starts."""
    with get_db() as conn:
        conn.execute(CREATE_STUDENTS_TABLE_SQL)
        conn.execute(CREATE_CONVERSATIONS_TABLE_SQL)
        conn.execute(CREATE_MESSAGES_TABLE_SQL)

        # Indexes make lookups faster as these tables grow.
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_student_id "
            "ON conversations(student_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id "
            "ON messages(conversation_id)"
        )
