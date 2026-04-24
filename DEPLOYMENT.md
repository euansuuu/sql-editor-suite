# SQL Editor - 部署指南

一个完整的 SQL 编辑器解决方案，包含前端和后端。

## 项目结构

```
.
├── sql-editor-backend/     # 后端 FastAPI 服务
│   ├── app/
│   ├── config/
│   ├── requirements.txt
│   └── README.md
└── vue-sql-editor/         # 前端 Vue 2 应用
    ├── src/
    ├── package.json
    └── README.md
```

## 环境要求

### 后端
- Python 3.10+
- pip
- 可选：Kerberos 客户端库（libkrb5-dev）

### 前端
- Node.js 16+
- npm 8+

---

## 后端部署

### 1. 安装依赖

```bash
cd sql-editor-backend
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=true

# 数据库配置（SQLite）
DATABASE_URL=sqlite:///./sql_app.db

# Kerberos 配置（可选）
KRB5_CONFIG=/etc/krb5.conf
KEYTAB_STORAGE_PATH=./keytabs
CCACHE_STORAGE_PATH=./ccache

# CORS 配置
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
```

### 3. 启动服务

```bash
# 开发模式
python -m app.main

# 使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问：http://localhost:8000/docs 查看 API 文档

### 4. 生产部署

使用 Gunicorn + Uvicorn：

```bash
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

使用 Docker：

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

---

## 前端部署

### 1. 安装依赖

```bash
cd vue-sql-editor
npm install
```

### 2. 配置 API 地址

编辑 `vue.config.js`：

```javascript
module.exports = {
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://your-backend-host:8000',  // 修改为你的后端地址
        changeOrigin: true
      }
    }
  }
}
```

### 3. 开发模式运行

```bash
npm run serve
```

访问：http://localhost:8080

### 4. 生产构建

```bash
npm run build
```

构建产物在 `dist/` 目录，可部署到 Nginx 等 Web 服务器。

### 5. Nginx 部署示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/vue-sql-editor/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # API 代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

---

## Kerberos 环境配置

### 1. 安装 Kerberos 客户端

```bash
# Ubuntu/Debian
sudo apt-get install -y krb5-user libkrb5-dev

# CentOS/RHEL
sudo yum install -y krb5-workstation krb5-libs
```

### 2. 配置 krb5.conf

编辑 `/etc/krb5.conf`：

```ini
[libdefaults]
    default_realm = EXAMPLE.COM
    dns_lookup_realm = false
    dns_lookup_kdc = false
    ticket_lifetime = 24h
    renew_lifetime = 7d
    forwardable = true

[realms]
    EXAMPLE.COM = {
        kdc = kdc.example.com
        admin_server = kdc.example.com
    }

[domain_realm]
    .example.com = EXAMPLE.COM
    example.com = EXAMPLE.COM
```

### 3. 验证 Kerberos

```bash
# 测试 kinit
kinit -kt /path/to/keytab principal@EXAMPLE.COM

# 查看票据
klist
```

---

## 数据源配置示例

### Hive Server 2

```json
{
  "name": "Hive Production",
  "type": "hive",
  "host": "hive-server.example.com",
  "port": 10000,
  "database": "default",
  "authType": "kerberos",
  "kerberosPrincipal": "hive/_HOST@EXAMPLE.COM",
  "kerberosKeytabPath": "/etc/security/keytabs/hive.keytab"
}
```

### Trino / Presto

```json
{
  "name": "Trino Cluster",
  "type": "trino",
  "host": "trino.example.com",
  "port": 8080,
  "database": "hive",
  "authType": "kerberos",
  "kerberosPrincipal": "trino@EXAMPLE.COM",
  "kerberosKeytabPath": "/etc/security/keytabs/trino.keytab"
}
```

### MySQL

```json
{
  "name": "MySQL Test",
  "type": "mysql",
  "host": "mysql.example.com",
  "port": 3306,
  "database": "test",
  "authType": "none",
  "username": "test_user"
}
```

---

## 系统服务配置

### 后端 systemd 服务

创建 `/etc/systemd/system/sql-editor-backend.service`：

```ini
[Unit]
Description=SQL Editor Backend
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/sql-editor-backend
Environment="PATH=/opt/sql-editor-backend/venv/bin"
ExecStart=/opt/sql-editor-backend/venv/bin/gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable sql-editor-backend
sudo systemctl start sql-editor-backend
sudo systemctl status sql-editor-backend
```

---

## 健康检查

### 后端健康检查

```bash
curl http://localhost:8000/health
```

预期响应：

```json
{
  "status": "ok",
  "timestamp": "..."
}
```

---

## 故障排查

### 1. 后端无法连接到数据源

- 检查网络连通性：`telnet host port`
- 验证 Kerberos 票据：`klist`
- 查看后端日志

### 2. 前端 API 请求失败

- 检查浏览器控制台网络请求
- 验证后端服务状态
- 检查 CORS 配置
- 确认代理配置正确

### 3. Kerberos 认证失败

- 检查 krb5.conf 配置
- 验证 Keytab 文件权限
- 确认 Principal 格式正确
- 查看 KDC 日志

---

## 升级指南

### 后端升级

```bash
cd sql-editor-backend
git pull
pip install -r requirements.txt
sudo systemctl restart sql-editor-backend
```

### 前端升级

```bash
cd vue-sql-editor
git pull
npm install
npm run build
# 重启 Nginx 或刷新静态资源
```

---

## 安全建议

1. **使用 HTTPS**：生产环境必须配置 SSL/TLS
2. **API 认证**：考虑添加 API Key 或 OAuth2 认证
3. **网络隔离**：将数据库和后端服务放在内网
4. **防火墙**：限制数据源端口仅后端可访问
5. **日志审计**：启用查询日志并定期审计
6. **权限控制**：数据库用户使用最小权限原则
