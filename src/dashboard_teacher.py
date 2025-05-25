from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from functools import wraps
from collections import defaultdict
import db_problems
import db_exam
import json
import requests
import os

dashboard_teacher_bp = Blueprint('dashboard_teacher', __name__, url_prefix='/teacher')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OPENROUTER_API_KEY_DIR = os.path.join(BASE_DIR, 'openrouter_apikey')

with open(OPENROUTER_API_KEY_DIR, 'r') as f:
    OPENROUTER_API_KEY = f.read().strip()

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


#
#
# ai generation problemsetting
#
#

@dashboard_teacher_bp.route('/ai_question_generation')
@teacher_required
def ai_question_generation():
    return render_template('subpages/teacher/ai_question_generation.html', username=session['username'])

@dashboard_teacher_bp.route('/ai_generate', methods=['POST'])
@teacher_required
def ai_generate():
    try:
        # 获取用户输入（前端传来的 prompt）
        user_input = request.json.get('prompt', '').strip()

        if not user_input:
            return jsonify({'error': 'Prompt 不能为空'}), 400

        # 构造 API 请求
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        final_prompt = f'''你要根据以下询问生成一道题目：{user_input}
        请给出题目内容、选项和答案。不要输出其它内容。输出格式如下：
        题目类型：选择题/多选题/判断题/简答题
        题目内容：题干、（如果是选择题或多选题，给出选项）
        题目答案：答案
        '''

        payload = {
            "model": "qwen/qwen3-30b-a3b:free",  # 你想用的模型
            "messages": [
                {"role": "user", "content": final_prompt}
            ]
        }
        # print(payload)
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )

        if response.status_code != 200:
            return jsonify({'error': '大模型请求失败', 'detail': response.text}), 500
        # print(response.json())
        data = response.json()
        # 提取模型回复
        reply = data['choices'][0]['message']['content']

        return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'error': '服务器错误', 'detail': str(e)}), 500


#
#
# exam management part in teacher's dashboard
#
#

@dashboard_teacher_bp.route('/exam_management')
@teacher_required
def exam_management():
    return render_template('subpages/teacher/exam_management.html', username=session['username'])

@dashboard_teacher_bp.route('/exam_management/create', methods=['POST'])
@teacher_required
def create_exam():
    data = request.get_json()
    paper_title = data.get('paper_title')
    exam_title = data.get('exam_title')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    description = data.get('description', '')

    if not all([paper_title, exam_title, start_time, end_time]):
        return jsonify({'success': False, 'error': '缺少必要字段'})

    try:
        identifier = db_problems.create_exam(exam_title, paper_title, start_time, end_time, description)
        return jsonify({'success': True, 'identifier': identifier})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard_teacher_bp.route('/exam_management/exams')
@teacher_required
def get_all_exams():
    exams = db_problems.get_all_exams()
    return jsonify(exams)

@dashboard_teacher_bp.route('/exam_management/<string:exam_identifier>/results_page')
@teacher_required
def exam_results_page(exam_identifier):
    return render_template('subpages/teacher/exam_results.html', exam_identifier=exam_identifier)

@dashboard_teacher_bp.route('/exam_management/<string:exam_identifier>/results')
@teacher_required
def view_exam_results(exam_identifier):
    try:
        raw_results = db_exam.get_answers_by_exam(exam_identifier)

        # name => {
        #   "submit_time": "...",
        #   "answers": [
        #       {"question_id": 1, "content": "题干", "answer": "A"},
        #       ...
        #   ]
        # }
        results_by_student = defaultdict(lambda: {"answers": [], "submit_time": None})

        for entry in raw_results:
            name = entry['name']
            qid = entry['question_id']
            answer = json.loads(entry['answer'])  # 可能是字符串或数组
            content = entry.get('question_content', '(题干缺失)')
            submit_time = entry['submit_time']

            results_by_student[name]["answers"].append({
                "question_id": qid,
                "content": content,
                "answer": answer
            })

            if results_by_student[name]["submit_time"] is None or submit_time > results_by_student[name]["submit_time"]:
                results_by_student[name]["submit_time"] = submit_time

        # 构造最终返回结果
        results_list = [
            {
                "name": name,
                "submit_time": data["submit_time"],
                "answers": data["answers"]
            }
            for name, data in results_by_student.items()
        ]

        return jsonify(success=True, results=results_list)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

#
#
# exam generation part in teacher's dashboard
#
#

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

@dashboard_teacher_bp.route('/paper/all')
@teacher_required
def get_all_exam_papers():
    papers = db_problems.get_all_papers()
    # papers 已是列表字典，直接 jsonify 返回
    return jsonify({'success': True, 'papers': papers})

@dashboard_teacher_bp.route('/paper/delete', methods=['POST'])
@teacher_required
def delete_exam_paper():
    data = request.get_json()
    title = data.get('title')
    if not title:
        return jsonify({'success': False, 'error': '标题缺失'})
    success = db_problems.delete_paper_by_title(title)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '删除失败，未找到对应试卷'})

@dashboard_teacher_bp.route('/paper/questions', methods=['POST'])
@teacher_required
def get_questions_by_paper():
    data = request.get_json()
    question_ids = data.get('question_ids', [])
    if not question_ids:
        return jsonify({'success': False, 'error': '未提供题目 ID 列表'})
    questions = db_problems.get_questions_by_ids(question_ids)
    return jsonify({'success': True, 'questions': questions})


#
#
# question management part in teacher's dashboard
#
#

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