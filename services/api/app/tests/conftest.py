"""pytest configuration · keeps tests pure-Python without a live DB."""
import os
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://defendable:defendable@localhost:5432/defendableos_test")
