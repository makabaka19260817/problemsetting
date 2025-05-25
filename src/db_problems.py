import sqlite3
import os
from flask import jsonify
import math

DB_PATH = 'questions.db'

def get_db_connection():
    # 如果数据库文件不存在，则初始化
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qtype TEXT NOT NULL,
            content TEXT NOT NULL,
            difficulty INTEGER NOT NULL,
            answer TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paper_questions (
            paper_id INTEGER,
            question_id INTEGER,
            position INTEGER,
            FOREIGN KEY (paper_id) REFERENCES papers(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_questions(page=1, per_page=20):
    offset = (page - 1) * per_page
    conn = get_db_connection()
    total_count = conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
    questions = conn.execute(
        'SELECT id, qtype, substr(content,1,50) AS content, difficulty FROM questions LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    conn.close()
    data = [dict(q) for q in questions]
    return {
        'questions': data,
        'total_pages': math.ceil(total_count / per_page),
        'current_page': page
    }

def get_question_detail(q_id):
    conn = get_db_connection()
    q = conn.execute('SELECT * FROM questions WHERE id = ?', (q_id,)).fetchone()
    conn.close()
    if not q:
        return None
    return dict(q)

def add_question(qtype, content, difficulty, answer):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO questions (qtype, content, difficulty, answer) VALUES (?, ?, ?, ?)',
        (qtype, content, difficulty, answer)
    )
    conn.commit()
    conn.close()

def edit_question(q_id, qtype, content, difficulty, answer):
    conn = get_db_connection()
    conn.execute(
        'UPDATE questions SET qtype=?, content=?, difficulty=?, answer=? WHERE id=?',
        (qtype, content, difficulty, answer, q_id)
    )
    conn.commit()
    conn.close()

def delete_question(q_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM questions WHERE id=?', (q_id,))
    conn.commit()
    conn.close()

def get_all_questions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, qtype, content, difficulty FROM questions')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_paper(title, question_ids):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO papers (title) VALUES (?)', (title,))
    paper_id = cursor.lastrowid

    for position, qid in enumerate(question_ids):
        cursor.execute('INSERT INTO paper_questions (paper_id, question_id, position) VALUES (?, ?, ?)',
                       (paper_id, qid, position))

    conn.commit()
    conn.close()
    return True
