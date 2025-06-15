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
        if session.get('role') != 'teacher':
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

@dashboard_teacher_bp.route('/students')
@teacher_required
def get_students_list():
    """获取所有学生用户列表"""
    try:
        from db_users import get_users_by_role
        students = get_users_by_role('student')
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard_teacher_bp.route('/exam_management/create', methods=['POST'])
@teacher_required
def create_exam():
    data = request.get_json()
    paper_id = data.get('paper_id')
    exam_title = data.get('exam_title')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    description = data.get('description', '')
    student_permissions = data.get('student_permissions', [])

    if not all([paper_id, exam_title, start_time, end_time]):
        return jsonify({'success': False, 'error': '缺少必要字段'})

    try:
        identifier = db_problems.create_exam(exam_title, paper_id, start_time, end_time, description)
        
        # 处理学生权限设置
        if student_permissions:
            for permission in student_permissions:
                if permission['student_name'] == '__ALL_STUDENTS__':
                    # 为所有学生设置相同的最大参加次数
                    from db_users import get_users_by_role
                    all_students = get_users_by_role('student')
                    max_attempts = permission.get('max_attempts', 1)
                    
                    for student in all_students:
                        db_exam.set_exam_permission(
                            identifier,
                            student['username'],
                            True,
                            max_attempts
                        )
                else:
                    # 为指定学生设置权限
                    db_exam.set_exam_permission(
                        identifier,
                        permission['student_name'],
                        permission.get('can_participate', True),
                        permission.get('max_attempts', 1)
                    )
        
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
        paper_id = db_problems.get_paper_id_by_exam_identifier(exam_identifier)
        # print(paper_id)
        if not paper_id:
            return jsonify(success=False, error='考试标识符无效'), 404

        scores = db_problems.get_question_scores_by_paper_id(paper_id)
        raw_results = db_exam.get_answers_by_exam(exam_identifier)
        # print(scores)
        # print(raw_results)

        results_by_student = defaultdict(lambda: {"answers": [], "submit_time": None})

        for entry in raw_results:
            name = entry['student_name']
            qid = entry['question_id']
            answerid = entry['id']
            answer = json.loads(entry['answer'])
            content = entry.get('question_content', '(题干缺失)')
            submit_time = entry['submit_time']
            score = scores.get(qid, 0)

            question = db_problems.get_question_detail(qid)
            answer_score = db_exam.get_student_answer_score_by_answerid(answerid)
            # print(answer_score)

            results_by_student[name]["answers"].append({
                "question_id": qid,
                "content": content,
                "answer": answer,
                "score": score,
                "question_type": question["qtype"],
                "correct_answer": question["answer"],
                "student_score": answer_score["student_score"],
                "is_graded": answer_score["is_graded"]
            })

            if results_by_student[name]["submit_time"] is None or submit_time > results_by_student[name]["submit_time"]:
                results_by_student[name]["submit_time"] = submit_time

        results_list = [
            {
                "name": name,
                "submit_time": data["submit_time"],
                "answers": data["answers"]
            }
            for name, data in results_by_student.items()
        ]
        print(results_list)
        
        return jsonify(success=True, results=results_list)

    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

@dashboard_teacher_bp.route('/exam_management/<string:exam_identifier>/grade', methods=['POST'])
@teacher_required
def grade_exam_answers(exam_identifier):
    """评分功能"""
    try:
        data = request.get_json()
        student_name = data.get('student_name')
        grades = data.get('grades', [])  # [{'question_id': 1, 'score': 5.0}, ...]
        
        if not student_name or not grades:
            return jsonify({'success': False, 'error': '缺少必要参数'})
        
        teacher_name = session['username']
        
        # 保存每道题的评分
        for grade in grades:
            db_exam.grade_question(
                exam_identifier, 
                student_name, 
                grade['question_id'], 
                grade['score'], 
                teacher_name
            )
        
        return jsonify({'success': True, 'message': '评分保存成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard_teacher_bp.route('/exam_management/<string:exam_identifier>/auto_grade', methods=['POST'])
@teacher_required
def auto_grade_exam(exam_identifier):
    """自动评判客观题"""
    try:
        graded_count = db_exam.auto_grade_objective_questions(exam_identifier)
        return jsonify({'success': True, 'graded_count': graded_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard_teacher_bp.route('/exam_management/<string:exam_identifier>/export')
@teacher_required
def export_exam_results(exam_identifier):
    """导出考试成绩"""
    try:
        from flask import make_response
        import csv
        import io
        
        # 获取考试结果
        results_response = view_exam_results(exam_identifier)
        if hasattr(results_response, 'json') and results_response.json.get('success'):
            results = results_response.json['results']
        else:
            return "导出失败：无法获取考试数据", 500
        
        # 创建CSV内容
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        writer.writerow(['学生姓名', '提交时间', '总得分', '满分', '得分率(%)', '题目数'])
        
        # 写入数据行
        for result in results:
            total_score = sum(ans.get('student_score', 0) for ans in result['answers'])
            max_score = sum(ans['score'] for ans in result['answers'])
            percentage = round((total_score / max_score) * 100, 2) if max_score > 0 else 0
            
            writer.writerow([
                result['name'],
                result['submit_time'],
                total_score,
                max_score,
                percentage,
                len(result['answers'])
            ])
        
        # 创建响应
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename=exam_results_{exam_identifier}.csv'
        
        return response
    except Exception as e:
        return f"导出失败：{str(e)}", 500

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

@dashboard_teacher_bp.route('/paper/save', methods=['POST'])
@teacher_required
def save_paper_api():
    data = request.get_json()
    title = data.get('title')
    questions_raw = data.get('questions')  # list of {"id": ..., "score": ...}

    if not title or not questions_raw:
        return jsonify({'success': False, 'message': '标题和题目不能为空'}), 400

    try:
        # 提取成 (id, score) 元组列表，并确保都是整数
        questions = [(int(q['id']), int(q['score'])) for q in questions_raw]
    except (KeyError, ValueError, TypeError):
        return jsonify({'success': False, 'message': '题目信息格式不正确'}), 400

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
    paper_id = data.get('paper_id')
    print(paper_id)
    if not paper_id:
        return jsonify({'success': False, 'error': '试卷ID缺失'})
    success = db_problems.delete_paper_by_id(paper_id)
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

@dashboard_teacher_bp.route('/question/add', methods=['POST'])
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

@dashboard_teacher_bp.route('/question/edit/<int:q_id>', methods=['PUT'])
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

@dashboard_teacher_bp.route('/question/delete/<int:q_id>', methods=['DELETE'])
@teacher_required
def delete_question_api(q_id):
    db_problems.delete_question(q_id)
    return jsonify({'message': '删除成功'})
