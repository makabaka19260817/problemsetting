from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from db_users import get_all_users, create_user, delete_user
from functools import wraps
import os
import csv
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join('../uploads', BASE_DIR)

dashboard_admin_bp = Blueprint('dashboard_admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return "权限不足", 403
        return f(*args, **kwargs)
    return wrapper

@dashboard_admin_bp.route('/user_management')
@admin_required
def user_management():
    users = get_all_users()
    return render_template('subpages/admin/user_management.html', users=users)

@dashboard_admin_bp.route('/add_user', methods=['POST'])
@admin_required
def add_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    create_user(username, email, password, role)
    return redirect(url_for('dashboard_admin.user_management'))

@dashboard_admin_bp.route('/delete_user', methods=['POST'])
@admin_required
def delete_user_route():
    username = request.form.get('username')
    if not username:
        flash('未提供用户名', 'error')
    else:
        success, message = delete_user(username)  # 确认delete_user函数是否返回success,message
        flash(message, 'success' if success else 'error')

    return redirect(url_for('dashboard_admin.user_management'))

@dashboard_admin_bp.route('/import_students', methods=['POST'])
@admin_required
def import_students():
    return _import_users_by_file('student')

@dashboard_admin_bp.route('/import_teachers', methods=['POST'])
@admin_required
def import_teachers():
    return _import_users_by_file('teacher')

def _import_users_by_file(role):
    if 'file' not in request.files:
        flash('未选择文件', 'error')
        return redirect(url_for('dashboard_admin.user_management'))

    file = request.files['file']
    if file.filename == '':
        flash('文件名为空', 'error')
        return redirect(url_for('dashboard_admin.user_management'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file.save(filepath)

    success_count = 0
    fail_count = 0

    try:
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                username = row.get('姓名') or row.get('用户名')  # 兼容两个字段名
                email = row.get('邮箱')
                password = row.get('密码')

                if username and email and password:
                    try:
                        create_user(username, email, password, role)
                        success_count += 1
                    except Exception as e:
                        fail_count += 1
                else:
                    fail_count += 1
    except Exception as e:
        flash(f'文件解析失败：{str(e)}', 'error')
        return redirect(url_for('dashboard_admin.user_management'))

    flash(f'{role}账号导入完成：成功 {success_count} 个，失败 {fail_count} 个。', 'success' if success_count > 0 else 'error')
    return redirect(url_for('dashboard_admin.user_management'))
