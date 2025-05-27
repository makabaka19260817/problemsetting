# 配置文件示例

## 必需的配置文件

在运行应用之前，请在 `src/` 目录下创建以下配置文件：

### 1. default_admin_password
创建文件：`src/default_admin_password`
内容：管理员账户的默认密码
```
your_admin_password_here
```

### 2. openrouter_apikey
创建文件：`src/openrouter_apikey`
内容：OpenRouter API密钥（用于AI功能）
```
your_openrouter_api_key_here
```

## 配置说明

- **default_admin_password**: 系统初始化时创建的管理员账户密码
- **openrouter_apikey**: 用于AI出题和智能批改功能的API密钥

## 安全提示

- 这些文件包含敏感信息，已在 `.gitignore` 中排除
- 请勿将真实的密钥和密码提交到公共仓库
- 在生产环境中，建议使用环境变量或专用的配置管理系统

## 示例创建命令

```powershell
# 创建管理员密码文件
echo "admin123" > src/default_admin_password

# 创建API密钥文件
echo "your_api_key_here" > src/openrouter_apikey
```
