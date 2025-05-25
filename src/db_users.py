# src/db_users.py
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'users.db')
ADMIN_PASSWORD_FILE = os.path.join(BASE_DIR, 'default_admin_password')

def read_admin_password():
    try:
        with open(ADMIN_PASSWORD_FILE, 'r', encoding='utf-8') as f:
            line = f.readline().strip()
            if not line:
                raise ValueError("默认管理员密码文件为空")
            return line
    except FileNotFoundError:
        raise FileNotFoundError(f"未找到默认密码文件: {ADMIN_PASSWORD_FILE}")
    except Exception as e:
        raise RuntimeError(f"读取管理员密码时出错: {e}")

def init_db():
    """初始化数据库，并写入默认管理员账号（仅首次创建）"""
    if not os.path.exists(DATABASE):
        admin_password = read_admin_password()
        password_hash = generate_password_hash(admin_password)

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0
                )
            ''')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@example.com', password_hash, 1))
            conn.commit()
        print("数据库已创建，并写入管理员用户：admin")

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_user(username, email, password, is_admin=False):
    password_hash = generate_password_hash(password)
    try:
        conn = get_db()
        conn.execute(
            'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
            (username, email, password_hash, int(is_admin))
        )
        conn.commit()
        return True, '注册成功'
    except sqlite3.IntegrityError:
        return False, '用户名或邮箱已存在'

def validate_user(username_or_email, password):
    conn = get_db()
    cur = conn.execute(
        'SELECT * FROM users WHERE username = ? OR email = ?',
        (username_or_email, username_or_email)
    )
    user = cur.fetchone()
    if user and check_password_hash(user['password_hash'], password):
        return True, {
            'username': user['username'],
            'is_admin': bool(user['is_admin'])
        }
    return False, '用户名或密码错误'

def get_all_users():
    """返回所有用户信息（用于管理员界面）"""
    conn = get_db()
    cur = conn.execute('SELECT username, email, is_admin FROM users ORDER BY id ASC')
    users = [
        {'username': row['username'], 'email': row['email'], 'is_admin': bool(row['is_admin'])}
        for row in cur.fetchall()
    ]
    return users

def delete_user(username):
    if username == 'admin':
        return False, '不能删除默认管理员账户'
    conn = get_db()
    conn.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    return True, '删除成功'
