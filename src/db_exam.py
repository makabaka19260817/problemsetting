import sqlite3
import json
import os
from datetime import datetime
from db_problems import get_question_detail

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'answers.db')

def init_db():
    """初始化作答数据库，建表等操作"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_identifier TEXT NOT NULL,
            student_name TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            submit_time TEXT NOT NULL
        )
    ''')
    
    # 新增评分表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_identifier TEXT NOT NULL,
            student_name TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            question_score INTEGER NOT NULL,
            student_score REAL DEFAULT 0,
            is_graded BOOLEAN DEFAULT FALSE,
            graded_by TEXT,
            grade_time TEXT
        )
    ''')
    
    # 新增考试参与记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_participations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_identifier TEXT NOT NULL,
            student_name TEXT NOT NULL,
            participation_count INTEGER DEFAULT 1,
            last_participation TEXT NOT NULL,
            UNIQUE(exam_identifier, student_name)
        )
    ''')
    
    # 新增考试权限表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_identifier TEXT NOT NULL,
            student_name TEXT NOT NULL,
            can_participate BOOLEAN DEFAULT TRUE,
            max_attempts INTEGER DEFAULT 1,
            created_time TEXT NOT NULL
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

def save_exam_answers(exam_identifier: str, student_name: str, answers: dict):
    """
    保存某次考试的所有答案，同时初始化评分记录
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    submit_time = datetime.now().isoformat()

    # 检查考试参与次数
    cursor.execute('''
        SELECT participation_count, max_attempts 
        FROM exam_participations ep
        LEFT JOIN exam_permissions epr ON ep.exam_identifier = epr.exam_identifier AND ep.student_name = epr.student_name
        WHERE ep.exam_identifier = ? AND ep.student_name = ?
    ''', (exam_identifier, student_name))
    participation_data = cursor.fetchone()
    
    max_attempts = 1  # 默认只能参加一次
    if participation_data:
        current_count = participation_data[0]
        max_attempts = participation_data[1] or 1
        if current_count >= max_attempts:
            conn.close()
            raise Exception(f"已达到最大参加次数限制({max_attempts}次)")
        
        # 更新参与次数
        cursor.execute('''
            UPDATE exam_participations 
            SET participation_count = participation_count + 1, last_participation = ?
            WHERE exam_identifier = ? AND student_name = ?
        ''', (submit_time, exam_identifier, student_name))
    else:
        # 首次参加，创建记录
        cursor.execute('''
            INSERT INTO exam_participations (exam_identifier, student_name, participation_count, last_participation)
            VALUES (?, ?, 1, ?)
        ''', (exam_identifier, student_name, submit_time))

    # 获取题目分值
    from db_problems import get_question_scores_by_exam_identifier
    question_scores = get_question_scores_by_exam_identifier(exam_identifier)

    for qid, ans in answers.items():
        # 保存答案
        cursor.execute('''
            INSERT INTO answers (exam_identifier, student_name, question_id, answer, submit_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (exam_identifier, student_name, qid, json.dumps(ans), submit_time))
        
        # 初始化评分记录
        question_score = question_scores.get(int(qid), 0)
        cursor.execute('''
            INSERT OR REPLACE INTO scores 
            (exam_identifier, student_name, question_id, question_score, student_score, is_graded)
            VALUES (?, ?, ?, ?, 0, FALSE)
        ''', (exam_identifier, student_name, qid, question_score))

    conn.commit()
    conn.close()

def get_answers_by_exam(exam_identifier: str):
    """
    查询某考试所有答卷，包含题目内容
    :param exam_identifier: 考试标识符
    :return: 每条记录包含 student_name, question_id, answer, submit_time, question_content
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

def grade_question(exam_identifier: str, student_name: str, question_id: int, score: float, graded_by: str):
    """给特定学生的特定题目打分"""
    conn = get_db_connection()
    cursor = conn.cursor()
    grade_time = datetime.now().isoformat()
    
    cursor.execute('''
        UPDATE scores 
        SET student_score = ?, is_graded = TRUE, graded_by = ?, grade_time = ?
        WHERE exam_identifier = ? AND student_name = ? AND question_id = ?
    ''', (score, graded_by, grade_time, exam_identifier, student_name, question_id))
    
    conn.commit()
    conn.close()

def auto_grade_objective_questions(exam_identifier: str):
    """自动评判客观题（选择题、判断题）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有答案
    cursor.execute('''
        SELECT DISTINCT student_name FROM answers WHERE exam_identifier = ?
    ''', (exam_identifier,))
    students = [row[0] for row in cursor.fetchall()]
    
    from db_problems import get_exam_questions_by_identifier
    questions = get_exam_questions_by_identifier(exam_identifier)
    
    auto_graded_count = 0
    
    for student in students:
        cursor.execute('''
            SELECT question_id, answer FROM answers 
            WHERE exam_identifier = ? AND student_name = ?
        ''', (exam_identifier, student))
        student_answers = dict(cursor.fetchall())
        for question in questions:
            if question['qtype'] in ['single_choice', 'multiple_choice', 'true_false', 'fill_blank']:
                qid = question['id']
                if qid in student_answers:
                    student_answer = json.loads(student_answers[qid])
                    correct_answer = question['answer']
                    
                    # 获取题目分值
                    cursor.execute('''
                        SELECT question_score FROM scores 
                        WHERE exam_identifier = ? AND student_name = ? AND question_id = ?
                    ''', (exam_identifier, student, qid))
                    question_score = cursor.fetchone()[0]
                    
                    # 判断正确性
                    is_correct = False
                    if question['qtype'] == 'single_choice':
                        is_correct = student_answer == correct_answer
                    elif question['qtype'] == 'multiple_choice':
                        is_correct = set(student_answer) == set(correct_answer)
                    elif question['qtype'] == 'true_false':
                        is_correct = student_answer == correct_answer
                    elif question['qtype'] == 'fill_blank':
                        # 填空题进行字符串比较（去除前后空格，不区分大小写）
                        is_correct = str(student_answer).strip().lower() == str(correct_answer).strip().lower()
                    
                    score = question_score if is_correct else 0
                    
                    # 更新分数
                    cursor.execute('''
                        UPDATE scores 
                        SET student_score = ?, is_graded = TRUE, graded_by = 'AUTO_SYSTEM', grade_time = ?
                        WHERE exam_identifier = ? AND student_name = ? AND question_id = ?
                    ''', (score, datetime.now().isoformat(), exam_identifier, student, qid))
                    
                    auto_graded_count += 1
    
    conn.commit()
    conn.close()
    return auto_graded_count

def get_student_exam_results(student_name: str):
    """获取学生的所有考试结果"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT 
            s.exam_identifier,
            SUM(s.student_score) as total_score,
            SUM(s.question_score) as max_score,
            COUNT(s.id) as question_count,
            MAX(a.submit_time) as submit_time
        FROM scores s
        JOIN answers a ON s.exam_identifier = a.exam_identifier AND s.student_name = a.student_name AND s.question_id = a.question_id
        WHERE s.student_name = ?
        GROUP BY s.exam_identifier
        ORDER BY submit_time DESC
    ''', (student_name,))
    
    results = []
    for row in cursor.fetchall():
        exam_info = dict(row)
        
        # 获取考试标题
        from db_problems import get_exam_title_by_identifier
        exam_info['exam_title'] = get_exam_title_by_identifier(exam_info['exam_identifier'])
        
        results.append(exam_info)
    
    conn.close()
    return results

def get_available_exams_for_student(student_name: str):
    """获取学生可以参加的考试列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有考试
    from db_problems import get_all_exams
    all_exams = get_all_exams()
    
    available_exams = []
    
    for exam in all_exams:
        exam_identifier = exam['identifier']
        
        # 检查权限
        cursor.execute('''
            SELECT can_participate, max_attempts FROM exam_permissions 
            WHERE exam_identifier = ? AND student_name = ?
        ''', (exam_identifier, student_name))
        permission = cursor.fetchone()
        
        # 检查已参加次数
        cursor.execute('''
            SELECT participation_count FROM exam_participations 
            WHERE exam_identifier = ? AND student_name = ?
        ''', (exam_identifier, student_name))
        participation = cursor.fetchone()
        
        can_participate = True
        max_attempts = 1
        current_attempts = 0
        
        if permission:
            can_participate = permission[0]
            max_attempts = permission[1] or 1
        
        if participation:
            current_attempts = participation[0]
        
        if can_participate and current_attempts < max_attempts:
            exam['current_attempts'] = current_attempts
            exam['max_attempts'] = max_attempts
            available_exams.append(exam)
    
    conn.close()
    return available_exams

def set_exam_permission(exam_identifier: str, student_name: str, can_participate: bool = True, max_attempts: int = 1):
    """设置单个学生的考试权限"""
    conn = get_db_connection()
    cursor = conn.cursor()
    created_time = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT OR REPLACE INTO exam_permissions (exam_identifier, student_name, can_participate, max_attempts, created_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (exam_identifier, student_name, can_participate, max_attempts, created_time))
    
    conn.commit()
    conn.close()

