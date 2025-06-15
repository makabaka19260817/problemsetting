# src/test_data_handler.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from db_problems import add_question, get_questions, init_db
from db_users import create_user, read_admin_password, generate_password_hash
import sqlite3
import os
from functools import wraps

test_data_bp = Blueprint('test_data', __name__, url_prefix='/test-data')

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return "权限不足", 403
        return f(*args, **kwargs)
    return wrapper

@test_data_bp.route('/')
@admin_required
def test_data_page():
    """测试数据管理页面"""
    return render_template('test_data.html')

@admin_required
@test_data_bp.route('/add-sample-questions', methods=['POST'])
def add_sample_questions():
    """添加示例题目数据"""
    
    # 示例题目数据
    sample_questions = [
        {
            'qtype': 'single_choice',
            'content': '下列哪个是Python的数据类型？\nA. int\nB. string\nC. float\nD. 以上都是',
            'difficulty': 1,
            'answer': 'D'
        },
        {
            'qtype': 'single_choice',
            'content': 'Flask是什么？\nA. 数据库\nB. Web框架\nC. 编程语言\nD. 操作系统',
            'difficulty': 2,
            'answer': 'B'
        },
        {
            'qtype': 'multiple_choice',
            'content': '以下哪些是常见的HTTP状态码？\nA. 200\nB. 404\nC. 500\nD. 999',
            'difficulty': 2,
            'answer': 'A,B,C'
        },
        {
            'qtype': 'essay',
            'content': 'Python中用于创建列表的符号是____，用于创建字典的符号是____。',
            'difficulty': 1,
            'answer': '[];{}'
        },
        {
            'qtype': 'true_false',
            'content': 'Python是一种解释型编程语言。',
            'difficulty': 1,
            'answer': '正确'
        },
        {
            'qtype': 'essay',
            'content': '请简述MVC设计模式的基本概念和优点。',
            'difficulty': 3,
            'answer': 'MVC是Model-View-Controller的缩写，是一种软件设计模式。Model负责数据处理，View负责用户界面，Controller负责业务逻辑。优点包括：代码结构清晰、易于维护、支持多视图、便于测试等。'
        },
        {
            'qtype': 'essay',
            'content': '编写一个Python函数，计算斐波那契数列的第n项。\n\n要求：\n1. 函数名为fibonacci\n2. 参数为正整数n\n3. 返回第n项的值',
            'difficulty': 3,
            'answer': 'def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)'
        },
        {
            'qtype': 'single_choice',
            'content': '在关系数据库中，下列哪个操作属于DML？\nA. CREATE TABLE\nB. DROP TABLE\nC. INSERT\nD. ALTER TABLE',
            'difficulty': 2,
            'answer': 'C'
        }
    ]
    
    try:
        for question in sample_questions:
            add_question(
                question['qtype'],
                question['content'],
                question['difficulty'],
                question['answer']
            )
        return jsonify({'success': True, 'message': f'成功添加{len(sample_questions)}道示例题目'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加失败：{str(e)}'})

@test_data_bp.route('/add-sample-users', methods=['POST'])
@admin_required
def add_sample_users():
    """添加示例用户数据"""
    
    # 示例用户数据
    sample_users = [
        {'username': 'teacher1', 'email': 'teacher1@example.com', 'password': '123456', 'role': 'teacher'},
        {'username': 'teacher2', 'email': 'teacher2@example.com', 'password': '123456', 'role': 'teacher'},
        {'username': 'student1', 'email': 'student1@example.com', 'password': '123456', 'role': 'student'},
        {'username': 'student2', 'email': 'student2@example.com', 'password': '123456', 'role': 'student'},
        {'username': 'student3', 'email': 'student3@example.com', 'password': '123456', 'role': 'student'},
    ]
    
    success_count = 0
    failed_users = []
    
    for user in sample_users:
        success, msg = create_user(user['username'], user['email'], user['password'], user['role'])
        if success:
            success_count += 1
        else:
            failed_users.append(f"{user['username']}: {msg}")
    
    message = f'成功添加{success_count}个用户'
    if failed_users:
        message += f'，失败{len(failed_users)}个：{"; ".join(failed_users)}'
    
    return jsonify({'success': True, 'message': message})

@test_data_bp.route('/clear-all-data', methods=['POST'])
@admin_required
def clear_all_data():
    """清空所有测试数据"""
    
    try:
        # 获取数据库连接
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # 清空题目数据库
        questions_db_path = os.path.join(BASE_DIR, 'questions_papers.db')
        if os.path.exists(questions_db_path):
            conn = sqlite3.connect(questions_db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM paper_questions')
            cursor.execute('DELETE FROM papers')
            cursor.execute('DELETE FROM questions')
            cursor.execute('DELETE FROM exams')
            conn.commit()
            conn.close()
        
        # 清空用户数据库（保留当前管理员）
        users_db_path = os.path.join(BASE_DIR, 'users.db')
        if os.path.exists(users_db_path):
            current_user_id = session.get('user', {}).get('id')
            conn = sqlite3.connect(users_db_path)
            cursor = conn.cursor()
            if current_user_id:
                cursor.execute('DELETE FROM users WHERE id != ?', (current_user_id,))
            else:
                cursor.execute('DELETE FROM users')
            admin_password = read_admin_password()
            password_hash = generate_password_hash(admin_password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@example.com', password_hash, 'admin'))
            conn.commit()
            conn.close()
        
        return jsonify({'success': True, 'message': '所有测试数据已清空'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'清空失败：{str(e)}'})

@test_data_bp.route('/generate-random-data', methods=['POST'])
@admin_required
def generate_random_data():
    """生成随机测试数据"""
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'})
            
        question_count = data.get('questionCount')
        user_count = data.get('userCount')
        
        # 验证和转换参数
        try:
            question_count = int(question_count) if question_count is not None else 10
            user_count = int(user_count) if user_count is not None else 5
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': '参数必须是有效的数字'})
        
        # 验证参数范围
        if question_count < 1 or question_count > 100:
            return jsonify({'success': False, 'message': '题目数量必须在1-100之间'})
        if user_count < 1 or user_count > 50:
            return jsonify({'success': False, 'message': '用户数量必须在1-50之间'})
        
        # 生成随机题目
        question_types = ['single_choice', 'multiple_choice', 'true_false', 'essay']
        difficulties = [1, 2, 3]
        
        for i in range(question_count):
            qtype = question_types[i % len(question_types)]
            content = f'这是第{i+1}道{qtype}的测试题目内容。'
            difficulty = difficulties[i % len(difficulties)]
            answer = f'答案{i+1}'
            
            add_question(qtype, content, difficulty, answer)
        
        # 生成随机用户
        for i in range(user_count):
            username = f'testuser{i+1}'
            email = f'testuser{i+1}@test.com'
            password = '123456'
            create_user(username, email, password)
        
        return jsonify({
            'success': True, 
            'message': f'成功生成{question_count}道题目和{user_count}个用户'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成失败：{str(e)}'})

@test_data_bp.route('/database-status')
@admin_required
def database_status():
    """获取数据库状态信息"""
    
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # 检查题目数据库
        questions_db_path = os.path.join(BASE_DIR, 'questions_papers.db')
        question_count = 0
        paper_count = 0
        exam_count = 0
        
        if os.path.exists(questions_db_path):
            conn = sqlite3.connect(questions_db_path)
            cursor = conn.cursor()
            
            # 安全地获取计数，处理可能的None值
            result = cursor.execute('SELECT COUNT(*) FROM questions').fetchone()
            question_count = result[0] if result and result[0] is not None else 0
            
            result = cursor.execute('SELECT COUNT(*) FROM papers').fetchone()
            paper_count = result[0] if result and result[0] is not None else 0
            
            result = cursor.execute('SELECT COUNT(*) FROM exams').fetchone()
            exam_count = result[0] if result and result[0] is not None else 0
            
            conn.close()
        
        # 检查用户数据库
        users_db_path = os.path.join(BASE_DIR, 'users.db')
        user_count = 0
        
        if os.path.exists(users_db_path):
            conn = sqlite3.connect(users_db_path)
            cursor = conn.cursor()
            
            result = cursor.execute('SELECT COUNT(*) FROM users').fetchone()
            user_count = result[0] if result and result[0] is not None else 0
            
            conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'questions': question_count,
                'papers': paper_count,
                'exams': exam_count,
                'users': user_count
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取状态失败：{str(e)}'})