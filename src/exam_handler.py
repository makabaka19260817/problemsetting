from flask import Blueprint, render_template, abort, request, jsonify
from db_problems import get_exam_questions_by_identifier
from db_exam import save_exam_answers
from datetime import datetime

exam_handler_bp = Blueprint('exam_handler', __name__, url_prefix='/exam')

@exam_handler_bp.route('/<string:identifier>', methods=['GET'])
def exam_page(identifier):
    questions = get_exam_questions_by_identifier(identifier)
    if questions is None:
        abort(404, '考试不存在或试卷不存在')

    return render_template('exam_page.html', identifier=identifier, questions=questions)

@exam_handler_bp.route('/<string:identifier>/submit', methods=['POST'])
def submit_exam(identifier):
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, error="请求数据为空"), 400

        name = data.get('name', '').strip()
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