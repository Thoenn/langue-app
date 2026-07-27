import sqlite3
import os
import json
import asyncio
from contextlib import asynccontextmanager
from config import DATABASE_PATH, DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "langue.db")

def get_sync_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

async def get_db():
    conn = await asyncio.to_thread(get_sync_conn)
    try:
        yield conn
    finally:
        await asyncio.to_thread(conn.close)

async def init_db():
    def _init():
        conn = get_sync_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL UNIQUE,
                emoji VARCHAR(10) DEFAULT '',
                order_index INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                french VARCHAR(500) NOT NULL,
                category_id INTEGER REFERENCES categories(id),
                subcategory VARCHAR(200) DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL REFERENCES words(id),
                language VARCHAR(10) NOT NULL,
                translation VARCHAR(500) NOT NULL,
                phonetic VARCHAR(300) DEFAULT '',
                example_fr TEXT DEFAULT '',
                example_target TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER REFERENCES words(id),
                language VARCHAR(10) NOT NULL,
                question_type VARCHAR(50) NOT NULL,
                question_text TEXT NOT NULL,
                correct_answer VARCHAR(500) NOT NULL,
                wrong_answers TEXT DEFAULT '[]',
                explanation TEXT DEFAULT '',
                source VARCHAR(50) DEFAULT 'system'
            );
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL REFERENCES words(id),
                language VARCHAR(10) NOT NULL,
                review_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0,
                last_reviewed TIMESTAMP,
                next_review TIMESTAMP,
                mastery_level REAL DEFAULT 0.0
            );
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER REFERENCES quiz_questions(id),
                language VARCHAR(10) NOT NULL,
                user_answer VARCHAR(500) NOT NULL,
                correct INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_spent REAL DEFAULT 0.0
            );
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER REFERENCES words(id),
                language VARCHAR(10) NOT NULL,
                mistake_type VARCHAR(50) DEFAULT 'translation',
                user_answer VARCHAR(500) NOT NULL,
                correct_answer VARCHAR(500) NOT NULL,
                context TEXT DEFAULT '',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed INTEGER DEFAULT 0,
                reviewed_at TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) DEFAULT '',
                messages TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_translations_language ON translations(language);
            CREATE INDEX IF NOT EXISTS idx_translations_word_id ON translations(word_id);
            CREATE INDEX IF NOT EXISTS idx_words_french ON words(french);
            CREATE INDEX IF NOT EXISTS idx_quiz_questions_language ON quiz_questions(language);
            CREATE INDEX IF NOT EXISTS idx_user_progress_word_lang ON user_progress(word_id, language);
        """)
        conn.commit()
        conn.close()
    await asyncio.to_thread(_init)

def dict_from_row(row):
    if row is None:
        return None
    return dict(row)
