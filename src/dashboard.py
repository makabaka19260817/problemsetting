from flask import Blueprint, render_template, session, redirect, url_for, request
from db_users import get_all_users, create_user, delete_user
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__)

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    is_admin = session.get('is_admin', False)
    if is_admin:
        return render_template('dashboard_admin.html', username=session['username'])
    else:
        return render_template('dashboard_teacher.html', username=session['username'])

@dashboard_bp.route('/user_management')
@login_required
def user_management():
    if not session.get('is_admin'):
        return "权限不足", 403
    users = get_all_users()
    return render_template('subpages/admin/user_management.html', users=users)

@dashboard_bp.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if not session.get('is_admin'):
        return "权限不足", 403
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    is_admin = int(request.form['is_admin']) == 1
    create_user(username, email, password, is_admin)
    return redirect(url_for('dashboard.user_management'))

@dashboard_bp.route('/delete_user', methods=['POST'])
@login_required
def delete_user_route():
    if not session.get('is_admin'):
        return "权限不足", 403

    username = request.form.get('username')
    if not username:
        flash('未提供用户名', 'error')
    else:
        success, message = delete_user_safe(username)
        flash(message, 'success' if success else 'error')

    return redirect(url_for('dashboard.user_management'))