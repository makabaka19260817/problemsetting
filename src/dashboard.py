# src/dashboard.py
from flask import Blueprint, render_template, session, redirect, url_for
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
