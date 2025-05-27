# 部署指南

## 系统要求
- Windows 10/11
- Python 3.8+
- 至少 100MB 磁盘空间

## 部署步骤

### 1. 克隆或下载项目
```bash
git clone <repository-url>
cd problemsetting
```

### 2. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 3. 初始化系统
```bash
python setup.py
```

### 4. 启动应用
```bash
# 方法1：使用批处理文件
start.bat

# 方法2：使用PowerShell脚本  
.\start.ps1

# 方法3：手动启动
cd src
python app.py
```

### 5. 访问系统
打开浏览器访问：`http://localhost:5000`

## 默认账户

### 管理员账户
- 用户名：`admin`
- 密码：在 `src/default_admin_password` 文件中（默认：admin123）

### 测试账户
在测试数据管理页面可以添加测试用户：
- teacher1@example.com / 123456
- student1@example.com / 123456
- 等等...

## 配置文件

### API密钥配置
编辑 `src/openrouter_apikey` 文件，添加您的OpenRouter API密钥以启用AI功能。

### 管理员密码
编辑 `src/default_admin_password` 文件来设置默认管理员密码。

## 功能使用

### 测试数据管理
1. 以管理员身份登录
2. 访问管理员控制台
3. 点击"测试数据管理"
4. 使用以下功能：
   - 添加示例题目数据
   - 添加示例用户数据
   - 生成随机测试数据
   - 监控数据库状态
   - 清理测试数据

### 教师功能
- 题库管理
- 试卷生成
- 考试管理
- AI辅助出题
- 成绩查看

### 学生功能
- 参加考试
- 查看成绩

## 故障排除

### 启动失败
1. 检查Python版本：`python --version`
2. 检查依赖安装：`pip list | findstr Flask`
3. 检查端口占用：`netstat -an | findstr 5000`

### 数据库问题
1. 删除 `src/*.db` 文件
2. 重新运行 `python setup.py`
3. 重启应用

### 编码问题
确保所有文件都使用UTF-8编码保存。

## 开发模式

### 启用调试模式
应用默认在调试模式下运行，代码更改会自动重载。

### 数据库位置
- 用户数据：`src/users.db`
- 题目数据：`src/questions_papers.db`
- 答题数据：`src/answers.db`

## 安全注意事项

1. 生产环境请更改默认管理员密码
2. 配置防火墙规则
3. 使用HTTPS
4. 定期备份数据库文件

## 技术支持

如遇问题，请检查：
1. Python环境是否正确
2. 依赖包是否完整安装
3. 配置文件是否正确设置
4. 网络连接是否正常
