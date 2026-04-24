# SQL Editor Suite

基于 Hue 改造的无用户系统 SQL 编辑器，支持多种数据源（Hive Server 2、Trino / Presto、Spark）和 Kerberos 认证。

---

## ✨ 特性

### 后端
- 🚀 **FastAPI** - 现代、高性能 Python Web 框架
- 🔌 **多数据源支持** - Hive Server 2、Trino / Presto、Spark、Impala
- 🔐 **完整 Kerberos 认证** - Keytab 管理、票据自动续期
- 📊 **异步 SQL 执行** - 状态追踪、取消、分页
- 📋 **元数据查询** - 数据库、表、列、分区信息
- 📚 **自动 API 文档** - Swagger / Redoc

### 前端
- 🎨 **Vue 3 + TypeScript** - 最新 Vue 技术栈
- ⚡ **Vite** - 极速开发体验
- 📝 **CodeMirror 6** - 专业 SQL 编辑器（语法高亮、自动补全、格式化）
- 📊 **查询结果表格** - 支持导出 CSV / Excel
- 🌳 **数据库浏览器** - 树形结构展示
- 📑 **多标签页支持** - 同时打开多个查询
- 🔧 **数据源管理** - CRUD + 连接测试
- 🎯 **Pinia** - 状态管理
- 💅 **Element Plus** - UI 组件库

---

## 📁 项目结构

```
sql-editor-suite/
├── sql-editor-backend/      # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── connectors/     # 数据源连接器
│   │   ├── services/       # 业务逻辑
│   │   ├── models.py       # 数据模型
│   │   ├── schemas/        # Pydantic 模式
│   │   └── main.py         # 入口文件
│   ├── config/             # 配置文件
│   ├── requirements.txt     # Python 依赖
│   ├── DEPLOYMENT_UBUNTU.md # Ubuntu 部署指南
│   └── README.md
│
├── vue-sql-editor-v3/      # Vue 3 + TypeScript 前端
│   ├── src/
│   │   ├── api/            # API 请求封装
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 公共组件
│   │   ├── stores/         # Pinia 状态
│   │   └── router/         # 路由
│   ├── package.json
│   └── README.md
│
├── DEPLOYMENT.md           # 完整部署指南
└── README.md               # 本文件
```

---

## 🚀 快速开始

### 后端启动

```bash
cd sql-editor-backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m app.main
```

访问：http://localhost:8000/docs

### 前端启动

```bash
cd vue-sql-editor-v3

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问：http://localhost:5173

---

## 📚 详细文档

- **完整部署指南**：[DEPLOYMENT.md](./DEPLOYMENT.md)
- **Ubuntu 部署指南**：[sql-editor-backend/DEPLOYMENT_UBUNTU.md](./sql-editor-backend/DEPLOYMENT_UBUNTU.md)
- **后端文档**：[sql-editor-backend/README.md](./sql-editor-backend/README.md)
- **前端文档**：[vue-sql-editor-v3/README.md](./vue-sql-editor-v3/README.md)

---

## 🔧 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **后端** | Python | 3.10 - 3.12 |
|        | FastAPI | 0.109.2 |
|        | SQLAlchemy | 2.0 |
|        | Pydantic | 2.6 |
|        | impyla | 0.18.0 |
|        | pyhive | 0.7.0 |
|        | trino | 0.328.0 |
|        | pure-sasl | 0.6.2 |
| **前端** | Vue | 3.4 |
|        | TypeScript | 5.3 |
|        | Vite | 5.0 |
|        | Pinia | 2.1 |
|        | Element Plus | 2.5 |
|        | CodeMirror | 6.0 |

---

## 🐳 Docker 部署

> 参考 [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 📄 License

MIT

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
