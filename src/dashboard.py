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
    role = session.get('role', False)
    print(role)
    if role == 'admin':
        return render_template('dashboard_admin.html', username=session['username'])
    elif role == 'teacher':
        return render_template('dashboard_teacher.html', username=session['username'])
    elif role == 'student':
        return render_template('dashboard_student.html', username=session['username'])
    else:
        pass

