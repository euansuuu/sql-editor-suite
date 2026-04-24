# Vue SQL Editor API 接口设计文档

## 目录

1. [通用约定](#通用约定)
2. [数据源管理 API](#数据源管理-api)
3. [查询执行 API](#查询执行-api)
4. [元数据 API](#元数据-api)
5. [查询历史 API](#查询历史-api)

---

## 通用约定

### Base URL: `/api`

### 请求头

| 名称 | 说明 | 示例 |
|------|------|------|
| Content-Type | 所有请求均为 JSON | `application/json` |
| Authorization | 认证 Token | `Bearer <token>` |

### 响应格式

所有接口统一响应格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | number | 状态码，0 表示成功，非 0 表示失败 |
| message | string | 状态说明 |
| data | any | 响应数据 |

### 错误码

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 数据源管理 API

### 1. 获取数据源列表

**接口**: `GET /datasources`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码，默认 1 |
| pageSize | number | 否 | 每页数量，默认 20 |
| keyword | string | 否 | 搜索关键词 |

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "id": "ds_001",
        "name": "Hive Production",
        "type": "hive",
        "host": "hive-prod.example.com",
        "port": 10000,
        "database": "default",
        "authType": "kerberos",
        "username": null,
        "password": null,
        "kerberos": {
          "principal": "hive/hive-prod.example.com@EXAMPLE.COM"
        },
        "createdAt": "2024-01-01T00:00:00.000Z",
        "updatedAt": "2024-01-01T00:00:00.000Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20
  }
}
```

### 2. 获取数据源详情

**接口**: `GET /datasources/:id`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 数据源 ID |

**响应示例**: 同列表项

### 3. 创建数据源

**接口**: `POST /datasources`

**请求体**:

```json
{
  "name": "MySQL Test",
  "type": "mysql",
  "host": "mysql-test.example.com",
  "port": 3306,
  "database": "test_db",
  "authType": "basic",
  "username": "admin",
  "password": "******"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 数据源名称 |
| type | string | 是 | SQL 方言：`hive`/`impala`/`spark`/`mysql`/`postgresql`/`trino` |
| host | string | 是 | 主机地址 |
| port | number | 是 | 端口号 |
| database | string | 是 | 默认数据库 |
| authType | string | 是 | 认证方式：`basic`/`kerberos` |
| username | string | 否 | 用户名（basic 认证时必填） |
| password | string | 否 | 密码（basic 认证时必填） |
| kerberos | object | 否 | Kerberos 配置（kerberos 认证时必填） |
| kerberos.principal | string | 是 | Kerberos Principal |
| kerberos.keytabPath | string | 否 | Keytab 文件路径 |

### 4. 更新数据源

**接口**: `PUT /datasources/:id`

**请求体**: 同创建接口，所有字段为可选

### 5. 删除数据源

**接口**: `DELETE /datasources/:id`

### 6. 测试数据源连接

**接口**: `POST /datasources/test`

**请求体**: 同创建接口

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "success": true,
    "message": "Connection successful"
  }
}
```

### 7. 上传 Keytab 文件

**接口**: `POST /datasources/keytab`

**请求**: `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | .keytab 文件 |

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "path": "/uploads/keytabs/xxxx.keytab",
    "filename": "user.keytab"
  }
}
```

---

## 查询执行 API

### 1. 执行 SQL 查询

**接口**: `POST /query/execute`

**请求体**:

```json
{
  "datasourceId": "ds_001",
  "database": "default",
  "sql": "SELECT * FROM users LIMIT 100",
  "maxRows": 10000
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| datasourceId | string | 是 | 数据源 ID |
| database | string | 是 | 数据库名称 |
| sql | string | 是 | SQL 语句 |
| maxRows | number | 否 | 最大返回行数，默认 10000 |

**响应示例**（同步执行）:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "query_12345",
    "sql": "SELECT * FROM users LIMIT 100",
    "datasourceId": "ds_001",
    "database": "default",
    "status": "success",
    "startTime": 1704067200000,
    "endTime": 1704067202500,
    "executionTime": 2500,
    "columns": [
      { "name": "id", "type": "int", "comment": "用户 ID" },
      { "name": "name", "type": "string", "comment": "用户名" },
      { "name": "email", "type": "string", "comment": "邮箱" }
    ],
    "rows": [
      { "id": 1, "name": "张三", "email": "zhang@example.com" },
      { "id": 2, "name": "李四", "email": "li@example.com" }
    ]
  }
}
```

**异步模式**:

如果查询预计耗时较长，可使用异步模式，响应中只返回查询 ID，前端轮询获取状态。

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "query_12345",
    "status": "running"
  }
}
```

### 2. 获取查询状态

**接口**: `GET /query/:id/status`

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "running",
    "progress": 50
  }
}
```

### 3. 获取查询结果

**接口**: `GET /query/:id/result`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码 |
| pageSize | number | 否 | 每页数量 |

**响应示例**: 同执行接口

### 4. 取消查询

**接口**: `POST /query/:id/cancel`

### 5. 导出查询结果

**接口**: `GET /query/:id/export`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| format | string | 是 | 导出格式：`csv`/`excel` |

**响应**: 文件流（`application/octet-stream`）

---

## 元数据 API

### 1. 获取数据库列表

**接口**: `GET /metadata/:datasourceId/databases`

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": ["default", "analytics", "data_warehouse"]
}
```

### 2. 获取数据库下的表列表

**接口**: `GET /metadata/:datasourceId/databases/:database/tables`

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "name": "users",
      "type": "table",
      "comment": "用户表"
    },
    {
      "name": "user_orders",
      "type": "view",
      "comment": "用户订单视图"
    }
  ]
}
```

### 3. 获取表详情

**接口**: `GET /metadata/:datasourceId/databases/:database/tables/:table`

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "name": "users",
    "type": "table",
    "comment": "用户表",
    "columns": [
      { "name": "id", "type": "int", "comment": "用户 ID" },
      { "name": "name", "type": "string", "comment": "用户名" },
      { "name": "email", "type": "string", "comment": "邮箱" },
      { "name": "created_at", "type": "timestamp", "comment": "创建时间" }
    ],
    "partitions": [
      { "name": "dt", "type": "string", "comment": "日期分区" }
    ],
    "rowCount": 1500000,
    "size": 256000000
  }
}
```

### 4. 获取表预览数据

**接口**: `GET /metadata/:datasourceId/databases/:database/tables/:table/preview`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | number | 否 | 返回行数，默认 100 |

### 5. 刷新元数据缓存

**接口**: `POST /metadata/:datasourceId/refresh`

**请求体**:

```json
{
  "database": "default",
  "table": "users"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| database | string | 否 | 指定数据库刷新，不传则刷新所有数据库 |
| table | string | 否 | 指定表刷新，不传则刷新数据库下所有表 |

---

## 查询历史 API

### 1. 获取查询历史列表

**接口**: `GET /query/history`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码，默认 1 |
| pageSize | number | 否 | 每页数量，默认 20 |
| datasourceId | string | 否 | 按数据源筛选 |
| keyword | string | 否 | 搜索关键词 |
| status | string | 否 | 按状态筛选 |

**响应示例**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "id": "query_12345",
        "sql": "SELECT * FROM users LIMIT 100",
        "datasourceId": "ds_001",
        "database": "default",
        "status": "success",
        "startTime": 1704067200000,
        "endTime": 1704067202500,
        "executionTime": 2500,
        "rowCount": 100
      }
    ],
    "total": 50,
    "page": 1,
    "pageSize": 20
  }
}
```

### 2. 获取查询详情

**接口**: `GET /query/history/:id`

**响应示例**: 同执行接口

---

## WebSocket 接口（可选）

对于长耗时查询，可使用 WebSocket 实时推送状态和结果。

### 连接地址

```
ws://your-host.com/api/ws/query
```

### 消息格式

**执行查询**:

```json
{
  "type": "execute",
  "data": {
    "datasourceId": "ds_001",
    "database": "default",
    "sql": "SELECT * FROM big_table"
  }
}
```

**状态推送**:

```json
{
  "type": "status",
  "data": {
    "queryId": "query_12345",
    "status": "running",
    "progress": 75
  }
}
```

**结果推送**:

```json
{
  "type": "result",
  "data": {
    "queryId": "query_12345",
    "status": "success",
    "columns": [...],
    "rows": [...]
  }
}
```
