# src/app.py
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from db_users import init_db, create_user, validate_user
from dashboard import dashboard_bp
from dashboard_admin import dashboard_admin_bp
from dashboard_teacher import dashboard_teacher_bp
from exam_handler import exam_handler_bp
from test_data_handler import test_data_bp
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, '../html'))
app.secret_key = 'supersecretkey'

@app.route('/')
def index():
    return redirect('/auth')

@app.route('/auth')
def login_register_page():
    return render_template('login_register.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.form  # 改用 form 方便跳转，前端提交时用表单
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        # 跳转到注册失败页面，传递错误信息
        return redirect(url_for('register_fail', message='请填写完整信息'))

    success, msg = create_user(username, email, password)
    if success:
        # 注册成功跳转
        return redirect(url_for('register_success'))
    else:
        # 注册失败跳转，传递失败原因
        return redirect(url_for('register_fail', message=msg))

@app.route('/register_success')
def register_success():
    return render_template('register_success.html')

@app.route('/register_fail')
def register_fail():
    # 从 URL 参数获取失败消息
    message = request.args.get('message', '注册失败')
    return render_template('register_fail.html', message=message)

@app.route('/login', methods=['POST'])
def login():
    data = request.form
    username_or_email = data.get('username')
    password = data.get('password')

    success, result = validate_user(username_or_email, password)
    if success:
        session['user'] = result
        session['role'] = result['role']
        session['username'] = result['username']
        return redirect(url_for('dashboard.dashboard'))  # 登录成功跳到 dashboard 首页
    else:
        # 登录失败跳转
        return redirect(url_for('login_fail', message=result))

@app.route('/login_fail')
def login_fail():
    message = request.args.get('message', '登录失败')
    return render_template('login_fail.html', message=message)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login_register_page'))

if __name__ == '__main__':
    print(os.path.join(BASE_DIR, '../html'))
    print(123123)
    init_db()
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(dashboard_admin_bp)
    app.register_blueprint(dashboard_teacher_bp)
    app.register_blueprint(exam_handler_bp)
    app.register_blueprint(test_data_bp)
    app.run(debug=True)
