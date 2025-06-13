from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from functools import wraps
import db_exam
import json

dashboard_student_bp = Blueprint('dashboard_student', __name__, url_prefix='/student')

def student_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'student':
            return "权限不足", 403
        return f(*args, **kwargs)
    return wrapper

@dashboard_student_bp.route('/available_exams')
@student_required
def available_exams():
    """显示可参加的考试列表"""
    return render_template('subpages/student/available_exams.html', username=session['username'])

@dashboard_student_bp.route('/api/available_exams')
@student_required
def api_available_exams():
    """获取学生可参加的考试列表API"""
    try:
        student_name = session['username']
        exams = db_exam.get_available_exams_for_student(student_name)
        return jsonify({'success': True, 'exams': exams})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard_student_bp.route('/exam_results')
@student_required
def exam_results():
    """显示考试成绩页面"""
    return render_template('subpages/student/exam_results.html', username=session['username'])

@dashboard_student_bp.route('/api/exam_results')
@student_required
def api_exam_results():
    """获取学生考试成绩API"""
    try:
        student_name = session['username']
        results = db_exam.get_student_exam_results(student_name)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard_student_bp.route('/recent_results')
@student_required
def recent_results():
    """获取最近的考试结果"""
    try:
        student_name = session['username']
        results = db_exam.get_student_exam_results(student_name)
        return jsonify({'success': True, 'results': results[:5]})  # 只返回最近5次
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard_student_bp.route('/exam_detail/<string:exam_identifier>')
@student_required
def exam_detail(exam_identifier):
    """查看具体考试的详细成绩"""
    try:
        student_name = session['username']
        
        # 获取学生在该考试中的答案和得分
        from db_exam import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                s.question_id, s.question_score, s.student_score, s.is_graded,
                a.answer, a.submit_time
            FROM scores s
            JOIN answers a ON s.exam_identifier = a.exam_identifier 
                AND s.student_name = a.name 
                AND s.question_id = a.question_id
            WHERE s.exam_identifier = ? AND s.student_name = ?
            ORDER BY s.question_id
        ''', (exam_identifier, student_name))
        
        details = []
        for row in cursor.fetchall():
            detail = dict(row)
            detail['answer'] = json.loads(detail['answer'])
            
            # 获取题目内容
            from db_problems import get_question_detail
            question = get_question_detail(detail['question_id'])
            if question:
                detail['question_content'] = question['content']
                detail['question_type'] = question['qtype']
                detail['correct_answer'] = question['answer']
            
            details.append(detail)
        
        conn.close()
        
        # 获取考试标题
        from db_problems import get_exam_title_by_identifier
        exam_title = get_exam_title_by_identifier(exam_identifier)
        
        return render_template('subpages/student/exam_detail.html', 
                             exam_identifier=exam_identifier,
                             exam_title=exam_title,
                             details=details,
                             username=session['username'])
    except Exception as e:
        return f"错误: {str(e)}", 500
