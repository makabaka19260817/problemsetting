from datetime import datetime
import sqlite3
import os
from flask import jsonify
import math
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'questions_papers.db')

def get_db_connection():
    """安全的数据库连接，带有重试机制和优化设置"""
    import time
    
    # 如果数据库文件不存在，则初始化
    if not os.path.exists(DB_PATH):
        init_db()
    
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10.0)
            # 优化设置
            conn.execute("PRAGMA journal_mode=WAL;")  # 启用WAL模式，减少锁定
            conn.execute("PRAGMA synchronous=NORMAL;")  # 平衡性能和安全性
            conn.execute("PRAGMA temp_store=MEMORY;")  # 临时文件存储在内存
            conn.execute("PRAGMA busy_timeout=30000;")  # 30秒超时
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                print(f"数据库锁定，{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                raise
    
    raise sqlite3.OperationalError("多次重试后仍无法连接数据库")

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
            score INTEGER,
            FOREIGN KEY (paper_id) REFERENCES papers(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_title TEXT NOT NULL,
            paper_title TEXT NOT NULL,
            paper_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            description TEXT,
            identifier TEXT UNIQUE NOT NULL,
            FOREIGN KEY (paper_id) REFERENCES papers(id)
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

def save_paper(title, question_items):  # question_items 是 [(question_id, score), ...]
    """保存试卷，使用安全的数据库连接管理"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 开始事务
            cursor.execute('BEGIN;')
            
            try:
                cursor.execute('INSERT INTO papers (title) VALUES (?)', (title,))
                paper_id = cursor.lastrowid

                for position, (qid, score) in enumerate(question_items):
                    cursor.execute('''
                        INSERT INTO paper_questions (paper_id, question_id, position, score)
                        VALUES (?, ?, ?, ?)
                    ''', (paper_id, qid, position, score))

                # 提交事务
                conn.commit()
                return True
                
            except Exception as e:
                # 回滚事务
                conn.rollback()
                print(f"保存试卷失败，已回滚: {e}")
                raise
                
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

def get_all_papers():
    conn = get_db_connection()
    papers_raw = conn.execute('SELECT id, title FROM papers').fetchall()

    result = []
    for paper in papers_raw:
        paper_id = paper['id']
        # print(paper_id)
        questions = conn.execute(
            'SELECT question_id, score FROM paper_questions WHERE paper_id = ? ORDER BY position',
            (paper_id,)
        ).fetchall()
        question_infos = [{'id': q['question_id'], 'score': q['score']} for q in questions]
        # print(question_ids)
        result.append({
            'title': paper['title'],
            'id': paper_id,
            'question_count': len(question_infos),
            'question_infos': question_infos
        })
        # print(result)

    conn.close()
    return result

def delete_paper_by_id(paper_id):
    conn = get_db_connection()
    cur = conn.cursor()

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

def create_exam(exam_title, paper_id, start_time, end_time, description):
    # 先检查时间格式合法且 end_time 晚于 start_time
    fmt = "%Y-%m-%dT%H:%M"
    try:
        dt_start = datetime.strptime(start_time, fmt)
        dt_end = datetime.strptime(end_time, fmt)
    except ValueError:
        raise ValueError("开始时间或结束时间格式不正确，正确格式示例：2025/06/16 10:00")

    if dt_end <= dt_start:
        raise ValueError("考试结束时间必须晚于开始时间")

    identifier = generate_exam_identifier()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取试卷标题
    cursor.execute('SELECT title FROM papers WHERE id = ?', (paper_id,))
    paper_result = cursor.fetchone()
    if not paper_result:
        conn.close()
        raise ValueError(f"未找到ID为 {paper_id} 的试卷")
    
    paper_title = paper_result[0]
    
    # 插入考试记录，包含paper_title
    cursor.execute('''
        INSERT INTO exams (exam_title, paper_title, paper_id, start_time, end_time, description, identifier)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (exam_title, paper_title, paper_id, start_time, end_time, description, identifier))
    conn.commit()
    conn.close()
    return identifier

def get_all_exams():
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT e.exam_title, p.title AS paper_title, e.start_time, e.end_time, e.description, e.identifier
        FROM exams e
        JOIN papers p ON e.paper_id = p.id
        ORDER BY e.start_time DESC
    ''').fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_exam_questions_by_identifier(identifier):
    conn = get_db_connection()

    exam = conn.execute('SELECT paper_id FROM exams WHERE identifier = ?', (identifier,)).fetchone()
    if not exam:
        conn.close()
        return None
    
    paper = conn.execute('SELECT title FROM papers WHERE id = ?', (exam['paper_id'],)).fetchone()
    paper_title = paper['title']

    paper_id = exam['paper_id']
    questions = conn.execute('''
        SELECT q.*, pq.score FROM questions q
        JOIN paper_questions pq ON q.id = pq.question_id
        WHERE pq.paper_id = ?
        ORDER BY pq.position
    ''', (paper_id,)).fetchall()

    conn.close()
    return [dict(row) for row in questions]

def get_paper_id_by_exam_identifier(identifier):
    conn = get_db_connection()
    exam = conn.execute('SELECT paper_id FROM exams WHERE identifier = ?', (identifier,)).fetchone()
    conn.close()
    if exam:
        return exam['paper_id']
    return None

def get_question_scores_by_paper_id(paper_id):
    conn = get_db_connection()
    rows = conn.execute('SELECT question_id, score FROM paper_questions WHERE paper_id = ?', (paper_id,)).fetchall()
    conn.close()
    return {row['question_id']: row['score'] for row in rows}

def get_question_scores_by_exam_identifier(exam_identifier: str):
    """根据考试标识符获取题目分值映射"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT pq.question_id, pq.score
        FROM exams e
        JOIN paper_questions pq ON e.paper_id = pq.paper_id
        WHERE e.identifier = ?
    ''', (exam_identifier,))
    
    scores = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return scores

def get_exam_title_by_identifier(exam_identifier: str):
    """根据考试标识符获取考试标题"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT exam_title FROM exams WHERE identifier = ?', (exam_identifier,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else "未知考试"