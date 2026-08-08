# -----------------------------------------------------------------
# config.py
#
# This is the ONLY place in the backend that reads environment
# variables. Every other file imports values from here instead of
# calling os.getenv() directly. That way, if a variable name ever
# changes, we only have to fix it in one place.
# -----------------------------------------------------------------

import os
from dotenv import load_dotenv

# load_dotenv() reads the ".env" file at the project root and puts
# its values into the environment, so os.getenv() can see them.
load_dotenv()

# ---- Database (SQLite) ----
# SQLite stores the whole database as a single file - no separate
# database server to install or configure. The file is created
# automatically the first time the app runs.
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "campusmate.db")

# ---- JWT authentication ----
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 1440 = 24 hours

# ---- CORS (which frontend URL is allowed to call this API) ----
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
