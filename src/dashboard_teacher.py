from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from functools import wraps
import db_problems

dashboard_teacher_bp = Blueprint('dashboard_teacher', __name__, url_prefix='/teacher')

def teacher_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('is_admin'):
            # 管理员不能访问老师专属页面，或者改成允许都能访问看需求
            return "权限不足", 403
        return f(*args, **kwargs)
    return wrapper

@dashboard_teacher_bp.route('/ai_question_generation')
@teacher_required
def ai_question_generation():
    return render_template('subpages/teacher/ai_question_generation.html', username=session['username'])

@dashboard_teacher_bp.route('/exam_management')
@teacher_required
def exam_management():
    return render_template('subpages/teacher/exam_management.html', username=session['username'])

@dashboard_teacher_bp.route('/paper_generation')
@teacher_required
def paper_generation():
    return render_template('subpages/teacher/paper_generation.html', username=session['username'])

@dashboard_teacher_bp.route('/questions/all')
@teacher_required
def all_questions():
    questions = db_problems.get_all_questions()
    return jsonify(questions)

@dashboard_teacher_bp.route('/paper', methods=['POST'])
@teacher_required
def save_paper_api():
    data = request.get_json()
    title = data.get('title')
    questions = data.get('questions')  # ordered list of question IDs
    if not title or not questions:
        return jsonify({'success': False, 'message': '标题和题目不能为空'}), 400
    success = db_problems.save_paper(title, questions)
    return jsonify({'success': success})

@dashboard_teacher_bp.route('/question_bank')
@teacher_required
def question_bank():
    return render_template('subpages/teacher/question_bank.html', username=session['username'])

@dashboard_teacher_bp.route('/questions', methods=['GET'])
@teacher_required
def questions_api():
    page = int(request.args.get('page', 1))
    data = db_problems.get_questions(page=page)
    return jsonify(data)

@dashboard_teacher_bp.route('/question/<int:q_id>', methods=['GET'])
@teacher_required
def question_detail_api(q_id):
    q = db_problems.get_question_detail(q_id)
    if not q:
        return jsonify({'error': '题目不存在'}), 404
    return jsonify(q)

@dashboard_teacher_bp.route('/question', methods=['POST'])
@teacher_required
def add_question_api():
    data = request.json
    required = ['qtype', 'content', 'difficulty', 'answer']
    if not all(field in data for field in required):
        return jsonify({'error': '缺少字段'}), 400
    db_problems.add_question(
        data['qtype'], data['content'], data['difficulty'], data['answer']
    )
    return jsonify({'message': '添加成功'}), 201

@dashboard_teacher_bp.route('/question/<int:q_id>', methods=['PUT'])
@teacher_required
def edit_question_api(q_id):
    data = request.json
    required = ['qtype', 'content', 'difficulty', 'answer']
    if not all(field in data for field in required):
        return jsonify({'error': '缺少字段'}), 400
    db_problems.edit_question(
        q_id, data['qtype'], data['content'], data['difficulty'], data['answer']
    )
    return jsonify({'message': '修改成功'})

@dashboard_teacher_bp.route('/question/<int:q_id>', methods=['DELETE'])
@teacher_required
def delete_question_api(q_id):
    db_problems.delete_question(q_id)
    return jsonify({'message': '删除成功'})