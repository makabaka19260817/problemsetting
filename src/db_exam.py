import sqlite3
import json
import os
from datetime import datetime

DB_PATH = 'answers.db'  # 你可以改成配置里的路径

def init_db():
    """初始化作答数据库，建表等操作"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_identifier TEXT NOT NULL,
            name TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            submit_time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    # 如果数据库文件不存在，则初始化
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def save_exam_answers(exam_identifier: str, name: str, answers: dict):
    """
    保存某次考试的所有答案
    :param exam_identifier: 考试标识符
    :param name: 参与者名字
    :param answers: {question_id: answer, ...}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    submit_time = datetime.now().isoformat()

    for qid, ans in answers.items():
        cursor.execute('''
            INSERT INTO answers (exam_identifier, name, question_id, answer, submit_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (exam_identifier, name, qid, json.dumps(ans), submit_time))

    conn.commit()
    conn.close()

from db_problems import get_question_detail

def get_answers_by_exam(exam_identifier: str):
    """
    查询某考试所有答卷，包含题目内容
    :param exam_identifier: 考试标识符
    :return: 每条记录包含 name, question_id, answer, submit_time, question_content
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM answers WHERE exam_identifier = ?', (exam_identifier,))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        row_dict = dict(row)
        q_detail = get_question_detail(row_dict['question_id'])
        row_dict['question_content'] = q_detail['content'] if q_detail else "(题目不存在)"
        results.append(row_dict)

    return results

