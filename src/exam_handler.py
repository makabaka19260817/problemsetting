from flask import Blueprint, render_template, abort, request, jsonify, session, redirect, url_for
from db_problems import get_exam_questions_by_identifier
from db_exam import save_exam_answers
from datetime import datetime
from functools import wraps

exam_handler_bp = Blueprint('exam_handler', __name__, url_prefix='/exam')

def student_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'student':
            return "权限不足", 403
        return f(*args, **kwargs)
    return wrapper

@exam_handler_bp.route('/<string:identifier>', methods=['GET'])
@student_required
def exam_page(identifier):
    questions, title = get_exam_questions_by_identifier(identifier)
    if questions is None:
        abort(404, '考试不存在或试卷不存在')

    return render_template('exam_page.html', identifier=identifier, questions=questions, title=title)

@exam_handler_bp.route('/<string:identifier>/submit', methods=['POST'])
@student_required
def submit_exam(identifier):
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, error="请求数据为空"), 400

        # name = data.get('name', '').strip()
        name = session.get('username')
        answers = data.get('answers', {})

        if not name:
            return jsonify(success=False, error="姓名不能为空"), 400
        if not answers:
            return jsonify(success=False, error="答案不能为空"), 400

        # 调用接口保存答案
        save_exam_answers(identifier, name, answers)

        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500