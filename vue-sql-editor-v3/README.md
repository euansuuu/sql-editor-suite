# Vue SQL Editor

一个基于 Vue 3 + TypeScript + CodeMirror 的现代化 SQL 查询编辑器，参考 Hue 的设计实现。

## 功能特性

### 核心功能
- 📝 **SQL 编辑器** - 基于 CodeMirror 6，支持语法高亮、自动补全
- 🔍 **查询执行** - 执行 SQL 并展示结果表格
- 📊 **结果导出** - 支持 CSV 和 Excel 格式导出
- 📁 **数据库浏览** - 树形结构展示数据库、表、视图
- 📋 **标签页管理** - 支持多标签页切换
- 🔄 **SQL 格式化** - 一键格式化 SQL 语句

### 数据源支持
- Hive SQL
- Impala SQL
- Spark SQL
- MySQL
- PostgreSQL
- Trino/Presto

### 认证方式
- 用户名密码认证
- Kerberos 认证

## 技术栈

- **框架**: Vue 3 + Composition API
- **语言**: TypeScript
- **构建工具**: Vite
- **状态管理**: Pinia
- **路由**: Vue Router
- **UI 组件库**: Element Plus
- **代码编辑器**: CodeMirror 6
- **HTTP 客户端**: Axios
- **Excel 导出**: SheetJS (xlsx)
- **SQL 格式化**: sql-formatter

## 快速开始

### 环境要求
- Node.js >= 16.0.0
- npm >= 7.0.0

### 安装依赖

```bash
cd vue-sql-editor
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

### 代码检查

```bash
npm run lint
```

## 项目结构

```
vue-sql-editor/
├── src/
│   ├── api/                      # API 接口封装
│   │   ├── request.ts            # Axios 实例封装
│   │   ├── datasource.ts         # 数据源相关 API
│   │   ├── query.ts              # 查询执行相关 API
│   │   └── metadata.ts           # 元数据相关 API
│   ├── components/               # 组件
│   │   ├── editor/              # 编辑器组件
│   │   │   └── SqlEditor.vue   # SQL 编辑器组件
│   │   ├── result/              # 查询结果组件
│   │   │   └── QueryResult.vue  # 查询结果表格
│   │   ├── sidebar/             # 侧边栏组件
│   │   │   └── DatabaseBrowser.vue # 数据库浏览器
│   │   ├── tabs/                # 标签页组件
│   │   │   └── TabBar.vue       # 标签栏
│   │   └── datasource/         # 数据源组件
│   │       └── DatasourceForm.vue # 数据源表单
│   ├── stores/                   # Pinia 状态管理
│   │   ├── datasource.ts       # 数据源状态
│   │   ├── tabs.ts              # 标签页状态
│   │   ├── editor.ts            # 编辑器状态
│   │   └── metadata.ts          # 元数据状态
│   ├── views/                    # 页面组件
│   │   ├── QueryEditor.vue    # 查询编辑器页面
│   │   ├── Datasources.vue     # 数据源管理页面
│   │   └── QueryHistory.vue   # 查询历史页面
│   ├── router/                   # 路由配置
│   │   └── index.ts
│   ├── types/                    # TypeScript 类型定义
│   │   └── index.ts
│   ├── utils/                    # 工具函数
│   ├── styles/                   # 全局样式
│   ├── App.vue                  # 根组件
│   └── main.ts                  # 入口文件
├── public/                       # 静态资源
├── .env                          # 环境变量
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## API 接口设计

### 数据源管理 API

#### 获取数据源列表
```
GET /api/datasources?page=1&pageSize=20
```

#### 创建数据源
```
POST /api/datasources
Body: {
  "name": "string",
  "type": "hive|impala|spark|mysql|postgresql|trino",
  "host": "string",
  "port": "number",
  "database": "string",
  "authType": "basic|kerberos",
  "username": "string",
  "password": "string",
  "kerberos": {
    "principal": "string",
    "keytabPath": "string"
  }
}
```

#### 测试数据源连接
```
POST /api/datasources/test
Body: { ...same as create
}
```

### 查询执行 API

#### 执行 SQL 查询
```
POST /api/query/execute
Body: {
  "datasourceId": "string",
  "database": "string",
  "sql": "string",
  "maxRows": 10000
}

Response: {
  "id": "string",
  "status": "running|success|failed",
  "columns": [{ "name": "string", "type": "string" }],
  "rows": [...],
  "executionTime": 1234,
  "error": "string"
}
```

#### 取消查询
```
POST /api/query/:id/cancel
```

#### 获取查询结果
```
GET /api/query/:id/result?page=1&pageSize=100
```

### 元数据 API

#### 获取数据库列表
```
GET /api/metadata/:datasourceId/databases
```

#### 获取表列表
```
GET /api/metadata/:datasourceId/databases/:database/tables
```

#### 获取表详情
```
GET /api/metadata/:datasourceId/databases/:database/tables/:table
```

## 配置说明

### 环境变量

在 `.env` 文件中配置：

```env
# API 基础路径
VITE_API_BASE_URL=/api

# 应用标题
VITE_APP_TITLE=Vue SQL Editor
```

### 代理配置

在 `vite.config.ts` 中配置开发代理：

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
})
```

## 使用说明

### 1. 创建数据源

1. 点击顶部导航「数据源管理」
2. 点击「新建数据源」按钮
3. 填写数据源信息
4. 点击「测试连接」验证连接是否成功
5. 点击「确定」保存

### 2. 执行 SQL 查询

1. 在查询编辑器页面
2. 选择数据源和数据库
3. 在编辑器中输入 SQL 语句
4. 点击「执行」按钮或快捷键执行
5. 查看下方的查询结果

### 3. 使用数据库浏览器

1. 在左侧数据库浏览器选择数据源
2. 点击数据库展开表列表
3. 点击表名查看表详情
4. 点击「插入 SELECT *」将查询插入编辑器

## 开发说明

### 状态管理

使用 Pinia 进行状态管理，分为以下几个 store：

- `datasource` - 数据源相关状态和操作
- `tabs` - 标签页状态管理
- `editor` - 编辑器配置和 SQL 格式化
- `metadata` - 数据库元数据缓存

### 组件开发

新增组件时请遵循以下约定：

1. 组件放在 `src/components/` 目录下
2. 使用 Composition API + `<script setup>` 语法
3. 使用 TypeScript 类型定义
4. 样式使用 scoped CSS

## 许可证

MIT
