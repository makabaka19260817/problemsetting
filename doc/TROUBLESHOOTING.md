# 🚀 Flask考试系统 - 常见问题解决指南

## ❌ "Method Not Allowed" 错误解决

### 常见原因和解决方案

#### 1. HTTP方法不匹配
**问题**: 使用了错误的HTTP方法访问路由
**解决**: 
- 页面访问使用 `GET` 方法
- 表单提交使用 `POST` 方法
- 数据更新使用 `PUT` 方法
- 数据删除使用 `DELETE` 方法

#### 2. 路由路径错误
**问题**: 访问了不存在的路由
**解决**: 访问 http://127.0.0.1:5000/debug/routes 查看所有可用路由

#### 3. 未登录访问受保护页面
**问题**: 访问需要登录的页面但未登录
**解决**: 先访问 http://127.0.0.1:5000/auth 登录

## 🔑 正确的访问流程

### 步骤1: 访问登录页面
```
URL: http://127.0.0.1:5000/
自动重定向到: http://127.0.0.1:5000/auth
```

### 步骤2: 使用管理员账号登录
```
用户名: admin
密码: admin123
```

### 步骤3: 访问相应功能
- **管理员**: http://127.0.0.1:5000/dashboard
- **教师功能**: http://127.0.0.1:5000/teacher/...
- **学生功能**: http://127.0.0.1:5000/student/...

## 📋 主要功能访问地址

### 认证相关
- 🔐 登录/注册: `/auth`
- 🚪 注销: `/logout` (POST方法)

### 管理员功能
- 👥 用户管理: `/admin/user_management`

### 教师功能  
- 📚 题库管理: `/teacher/question_bank`
- 🤖 AI出题: `/teacher/ai_question_generation`
- 📝 组卷管理: `/teacher/paper_generation`
- 📊 考试管理: `/teacher/exam_management`

### 学生功能
- 📋 可参加考试: `/student/available_exams`
- 📈 考试成绩: `/student/exam_results`

### 考试相关
- 💯 参加考试: `/exam/<考试标识符>`

## 🛠️ 调试工具

### 路由调试页面
访问: http://127.0.0.1:5000/debug/routes
功能: 查看所有可用路由和HTTP方法

### 数据库状态检查
```bash
cd C:\SEProject\problemsetting\src
python -c "
import sqlite3
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('SELECT username, role FROM users')
print('用户列表:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')
conn.close()
"
```

## 🚨 紧急重置

如果系统出现严重问题，可以重置数据库：

```bash
cd C:\SEProject\problemsetting\src
python -c "
import os
if os.path.exists('users.db'): os.remove('users.db')
if os.path.exists('questions_papers.db'): os.remove('questions_papers.db')
if os.path.exists('answers.db'): os.remove('answers.db')
print('数据库已清理')
"
python migrate_db.py
```

## 📞 技术支持

如果问题仍然存在：
1. 检查终端是否有错误信息
2. 确认Python环境和依赖完整
3. 访问调试页面查看路由状态
4. 重启Flask应用

---
*更新时间: 2025年6月13日*
