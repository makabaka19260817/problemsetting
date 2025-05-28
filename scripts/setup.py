import threading
import time
import sys
import os
from flask import Flask, request, jsonify, render_template, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_PASS_PATH = os.path.join(BASE_DIR, '../src/default_admin_password')
APIKEY_PATH = os.path.join(BASE_DIR, '../src/openrouter_apikey')
app = Flask(__name__, template_folder=BASE_DIR)

def delayed_exit(seconds=2):
    def _exit():
        time.sleep(seconds)
        print("正在退出后端服务...")
        os._exit(0)  # 或使用 sys.exit(0)
    threading.Thread(target=_exit, daemon=True).start()

@app.route('/')
def index():
    return redirect('/setup')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    def is_configured():
        try:
            with open(ADMIN_PASS_PATH, 'r', encoding='utf-8') as f:
                admin_pass = f.read().strip()
            with open(APIKEY_PATH, 'r', encoding='utf-8') as f:
                api_key = f.read().strip()
            return bool(admin_pass) and bool(api_key)
        except FileNotFoundError:
            return False

    if is_configured():
        delayed_exit()  # 延迟退出
        return render_template('setup_exist.html')

    if request.method == 'GET':
        return render_template('setup.html')

    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'message': '请求体必须是 JSON 格式'}), 400

        admin_password = data.get('adminPassword', '').strip()
        api_key = data.get('apiKey', '').strip()

        if not admin_password or not api_key:
            return jsonify({'message': '管理员密码和 API Key 不能为空'}), 400

        try:
            os.makedirs('./src', exist_ok=True)
            with open(ADMIN_PASS_PATH, 'w', encoding='utf-8') as f:
                f.write(admin_password)

            with open(APIKEY_PATH, 'w', encoding='utf-8') as f:
                f.write(api_key)
        except Exception as e:
            return jsonify({'message': f'写入文件失败: {str(e)}'}), 500

        delayed_exit()  # 成功配置后退出
        return jsonify({'message': '配置成功，请运行 python ./src/app.py'})


if __name__ == '__main__':
    print(BASE_DIR)
    app.run(debug=True)
