import sqlite3
from fastapi import HTTPException
from typing import Optional
from datetime import datetime
import os

# DB_PATH = "app/database.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def init_database():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS users(
                 user_id INTEGER PRIMARY KEY,
                 username TEXT UNIQUE NOT NULL,
                 full_name TEXT NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 hashed_password TEXT NOT NULL,
                 date_of_birth TEXT NOT NULL,
                 location TEXT NOT NULL,
                 created_at TEXT NOT NULL)"""
                 
)
    conn.commit()
    conn.close()



def create_user(username: str, full_name: str, email: str, hashed_password: str, date_of_birth: str, location: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO users (username, full_name, email, hashed_password, date_of_birth, location, created_at) VALUES (?,?,?,?,?,?,?)",
                     (username, full_name, email, hashed_password, date_of_birth, location, datetime.now().isoformat()))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    finally:
        conn.close()

def get_user(username: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE username = ?",
                       (username,)).fetchone()
    conn.close()
    if row:
        return {"username": row["username"], "full_name": row["full_name"], "email":row["email"], "hashed_password" : row["hashed_password"], "date_of_birth": row["date_of_birth"], "location":row["location"], "created_at": row["created_at"]}
    return None

    