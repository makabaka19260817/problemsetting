from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from db_users import get_all_users, create_user, delete_user
from functools import wraps

dashboard_admin_bp = Blueprint('dashboard_admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if not session.get('is_admin'):
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
    is_admin = int(request.form.get('is_admin', 0)) == 1
    create_user(username, email, password, is_admin)
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
