import sqlite3
import os
from flask import jsonify
import math
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'questions_papers.db')

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_title TEXT NOT NULL,
            paper_title TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            description TEXT,
            identifier TEXT UNIQUE NOT NULL
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

def get_all_papers():
    conn = get_db_connection()
    papers_raw = conn.execute('SELECT id, title FROM papers').fetchall()

    result = []
    for paper in papers_raw:
        paper_id = paper['id']
        # print(paper_id)
        questions = conn.execute(
            'SELECT question_id FROM paper_questions WHERE paper_id = ? ORDER BY position',
            (paper_id,)
        ).fetchall()
        question_ids = [q['question_id'] for q in questions]
        # print(question_ids)
        result.append({
            'title': paper['title'],
            'question_count': len(question_ids),
            'question_ids': question_ids
        })
        # print(result)

    conn.close()
    return result

def delete_paper_by_title(title):
    conn = get_db_connection()
    cur = conn.cursor()

    # 获取 paper_id
    paper_row = cur.execute('SELECT id FROM papers WHERE title = ?', (title,)).fetchone()
    if not paper_row:
        conn.close()
        return False

    paper_id = paper_row['id']

    # 删除 paper_questions 中的关联记录
    cur.execute('DELETE FROM paper_questions WHERE paper_id = ?', (paper_id,))

    # 删除 papers 表中的记录
    cur.execute('DELETE FROM papers WHERE id = ?', (paper_id,))

    conn.commit()
    success = cur.rowcount > 0
    conn.close()
    return success

def get_questions_by_ids(ids):
    if not ids:
        return []

    conn = get_db_connection()
    placeholders = ','.join(['?'] * len(ids))
    query = f'SELECT * FROM questions WHERE id IN ({placeholders})'
    rows = conn.execute(query, ids).fetchall()
    conn.close()

    # 保证返回顺序与 ids 一致
    row_map = {row['id']: dict(row) for row in rows}
    return [row_map[qid] for qid in ids if qid in row_map]

def generate_exam_identifier():
    return str(uuid.uuid4())

def create_exam(exam_title, paper_title, start_time, end_time, description):
    identifier = generate_exam_identifier()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO exams (exam_title, paper_title, start_time, end_time, description, identifier)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (exam_title, paper_title, start_time, end_time, description, identifier))
    conn.commit()
    conn.close()
    return identifier

def get_all_exams():
    conn = get_db_connection()
    rows = conn.execute('SELECT exam_title, paper_title, start_time, end_time, description, identifier FROM exams ORDER BY start_time DESC').fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_exam_questions_by_identifier(identifier):
    conn = get_db_connection()

    exam = conn.execute('SELECT paper_title FROM exams WHERE identifier = ?', (identifier,)).fetchone()
    if not exam:
        conn.close()
        return None

    paper_title = exam['paper_title']
    paper_row = conn.execute('SELECT id FROM papers WHERE title = ?', (paper_title,)).fetchone()
    if not paper_row:
        conn.close()
        return None

    paper_id = paper_row['id']
    questions = conn.execute('''
        SELECT q.* FROM questions q
        JOIN paper_questions pq ON q.id = pq.question_id
        WHERE pq.paper_id = ?
        ORDER BY pq.position
    ''', (paper_id,)).fetchall()

    conn.close()
    return questions
