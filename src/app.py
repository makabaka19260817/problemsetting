# src/app.py
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from db_users import init_db, create_user, validate_user
from dashboard import dashboard_bp
from dashboard_admin import dashboard_admin_bp
from dashboard_teacher import dashboard_teacher_bp
from dashboard_student import dashboard_student_bp
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

@app.route('/debug/routes')
def debug_routes():
    """调试路由 - 显示所有可用路由"""
    routes_info = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            routes_info.append({
                'rule': rule.rule,
                'methods': methods,
                'endpoint': rule.endpoint
            })
    
    # 生成简单的HTML页面
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask路由调试</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .methods { color: #007bff; }
            .endpoint { color: #28a745; }
        </style>
    </head>
    <body>
        <h1>🔍 Flask应用路由调试</h1>
        <p>以下是所有可用的路由：</p>
        <table>
            <tr>
                <th>路由路径</th>
                <th>HTTP方法</th>
                <th>端点名称</th>
            </tr>
    '''
    
    for route in sorted(routes_info, key=lambda x: x['rule']):
        html += f'''
            <tr>
                <td><code>{route['rule']}</code></td>
                <td class="methods">{route['methods']}</td>
                <td class="endpoint">{route['endpoint']}</td>
            </tr>
        '''
    
    html += '''
        </table>
        <br>
        <h3>📝 使用说明：</h3>
        <ul>
            <li><strong>GET</strong> - 用于访问页面和获取数据</li>
            <li><strong>POST</strong> - 用于提交表单和创建数据</li>
            <li><strong>PUT</strong> - 用于更新数据</li>
            <li><strong>DELETE</strong> - 用于删除数据</li>
        </ul>
        
        <h3>🚀 快速链接：</h3>
        <ul>
            <li><a href="/">主页</a></li>
            <li><a href="/auth">登录页面</a></li>
            <li><a href="/dashboard">仪表板</a> (需要登录)</li>
        </ul>
    </body>
    </html>
    '''
    
    return html

if __name__ == '__main__':
    print(os.path.join(BASE_DIR, '../html'))
    print(123123)
    init_db()
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(dashboard_admin_bp)
    app.register_blueprint(dashboard_teacher_bp)
    app.register_blueprint(dashboard_student_bp)
    app.register_blueprint(exam_handler_bp)
    app.register_blueprint(test_data_bp)
    app.run(debug=True)
