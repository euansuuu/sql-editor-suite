# SQL Editor Backend

无用户系统的 SQL 编辑器后端服务，基于 Hue 的后端架构提取 SQL 执行核心能力。

## 功能特性

### 1. SQL 执行引擎
- ✅ 异步查询执行
- ✅ 查询状态跟踪
- ✅ 结果分页获取
- ✅ 查询取消功能
- ✅ 查询历史记录

### 2. 数据源管理
- ✅ 数据源 CRUD
- ✅ 数据源连接测试
- ✅ 数据源配置持久化
- ✅ 支持多类型数据源连接器

### 3. Kerberos 认证管理
- ✅ Kerberos ticket 管理（kinit）
- ✅ Keytab 文件上传和管理
- ✅ Ticket 缓存管理
- ✅ 票据自动续期功能

### 4. 元数据查询
- ✅ 数据库列表
- ✅ 表列表
- ✅ 表结构/列信息
- ✅ 分区信息

## 技术栈

- Python 3.10+
- FastAPI (REST API 框架)
- SQLAlchemy (ORM)
- Pydantic (数据验证)
- pyhive (Hive/Impala 客户端)
- impyla (HiveServer2 连接器)
- Uvicorn (ASGI 服务器)

## 已实现的数据源连接器

| 数据源类型 | 状态 | 备注 |
|-----------|------|------|
| HiveServer2 | ✅ 已实现 | 支持 Kerberos 认证 |
| Impala | ⏳ 待实现 | 可基于 HiveServer2 扩展 |
| Spark SQL | ⏳ 待实现 | 基于 Livy |
| Trino/Presto | ⏳ 待实现 | |
| JDBC | ⏳ 待实现 | |

## 项目结构

```
sql-editor-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 入口
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── datasource.py       # 数据源管理 API
│   │   ├── sql.py              # SQL 执行 API
│   │   ├── metadata.py         # 元数据查询 API
│   │   └── kerberos.py         # Kerberos 管理 API
│   ├── connectors/             # 数据源连接器
│   │   ├── __init__.py
│   │   ├── base.py            # 基类
│   │   └── hiveserver2.py     # HiveServer2 实现
│   ├── models/                # 数据模型
│   │   └── __init__.py
│   ├── schemas/               # Pydantic Schema
│   │   └── __init__.py
│   ├── services/              # 业务逻辑
│   │   ├── __init__.py
│   │   ├── kerberos.py        # Kerberos 管理服务
│   │   └── execution.py       # SQL 执行管理服务
│   └── utils/                 # 工具函数
│       └── __init__.py
├── config/                    # 配置文件
│   ├── __init__.py
│   └── settings.py
├── requirements.txt
├── .env.example
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，根据需要修改配置
```

### 3. 启动服务

```bash
# 开发模式
python -m app.main

# 或使用 uvicorn 直接启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## API 接口概览

### SQL 执行相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sql/execute` | 执行 SQL |
| GET | `/api/sql/status/{id}` | 获取查询状态 |
| GET | `/api/sql/result/{id}` | 获取查询结果 |
| POST | `/api/sql/cancel/{id}` | 取消查询 |
| GET | `/api/sql/history` | 查询历史列表 |

### 数据源管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/datasources` | 获取所有数据源 |
| POST | `/api/datasources` | 创建数据源 |
| GET | `/api/datasources/{id}` | 获取单个数据源 |
| PUT | `/api/datasources/{id}` | 更新数据源 |
| DELETE | `/api/datasources/{id}` | 删除数据源 |
| POST | `/api/datasources/{id}/test` | 测试连接 |

### 元数据查询

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/metadata/{id}/databases` | 数据库列表 |
| GET | `/api/metadata/{id}/tables/{db}` | 表列表 |
| GET | `/api/metadata/{id}/columns/{db}/{table}` | 列信息 |
| GET | `/api/metadata/{id}/partitions/{db}/{table}` | 分区信息 |

### Kerberos 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/kerberos/kinit` | 获取 Kerberos ticket |
| GET | `/api/kerberos/status` | Kerberos 状态 |
| POST | `/api/kerberos/keytab/upload` | 上传 Keytab |
| POST | `/api/kerberos/destroy` | 销毁票据 |
| POST | `/api/kerberos/auto-renewal/start` | 启动自动续期 |
| POST | `/api/kerberos/auto-renewal/stop` | 停止自动续期 |

## 使用示例

### 1. 创建 HiveServer2 数据源

```bash
curl -X POST http://localhost:8000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-hive",
    "type": "hiveserver2",
    "host": "hive-server.example.com",
    "port": 10000,
    "database": "default",
    "use_kerberos": true,
    "kerberos_principal": "hive/_HOST@EXAMPLE.COM"
  }'
```

### 2. 测试连接

```bash
curl -X POST http://localhost:8000/api/datasources/1/test
```

### 3. 上传 Keytab 文件

```bash
curl -X POST "http://localhost:8000/api/kerberos/keytab/upload?principal=user@EXAMPLE.COM" \
  -F "file=@user.keytab"
```

### 4. 获取 Kerberos 票据

```bash
curl -X POST http://localhost:8000/api/kerberos/kinit \
  -H "Content-Type: application/json" \
  -d '{
    "principal": "user@EXAMPLE.COM",
    "keytab_path": "./keytabs/user_EXAMPLE_COM.keytab"
  }'
```

### 5. 执行 SQL

```bash
curl -X POST http://localhost:8000/api/sql/execute \
  -H "Content-Type: application/json" \
  -d '{
    "datasource_id": 1,
    "sql": "SELECT * FROM test_table LIMIT 10",
    "max_rows": 1000
  }'
```

### 6. 查询执行状态

```bash
curl http://localhost:8000/api/sql/status/{query_id}
```

### 7. 获取查询结果

```bash
curl "http://localhost:8000/api/sql/result/{query_id}?offset=0&limit=100"
```

## 扩展新的数据源连接器

要添加新的数据源连接器：

1. 在 `app/connectors/` 下创建新的连接器文件
2. 继承 `BaseConnector` 基类并实现所有抽象方法
3. 在 `app/connectors/__init__.py` 中导出新连接器
4. 在 `app/services/execution.py` 的 `connector_map` 中添加映射

示例：

```python
# app/connectors/new_source.py
from .base import BaseConnector

class NewSourceConnector(BaseConnector):
    def connect(self):
        # 实现连接逻辑
        pass

    # 实现其他抽象方法...
```

## Kerberos 配置说明

### 前置条件

1. 系统已安装 Kerberos 客户端（`krb5-user`）
2. `/etc/krb5.conf` 配置正确
3. 具有有效的 Keytab 文件或密码

### 自动续期功能

服务提供票据自动续期功能，会在票据过期前 1 小时自动续期。需要：
1. 上传或指定有效的 Keytab 文件
2. 调用 `/api/kerberos/auto-renewal/start` 启动自动续期

## 注意事项

1. **密码安全**: 数据源密码在数据库中以明文存储，生产环境建议加密处理
2. **Kerberos**: 确保服务器时间与 KDC 时间同步，否则会导致认证失败
3. **查询超时**: 默认查询超时时间为 3600 秒（1 小时），可在配置中修改
4. **结果存储**: 查询结果默认存储在 `./query_results/` 目录下，定期清理
5. **并发控制**: 当前使用简单线程模型，高并发场景建议使用任务队列

## License

MIT

---

## Python 3.12 兼容性说明

### SASL 依赖问题

`sasl==0.3.1` 与 Python 3.12 不兼容（缺少 `longintrepr.h` 头文件），本项目已改用 `pure-sasl`（纯 Python 实现）。

### 额外配置

安装依赖后，需要确保 `thrift-sasl` 使用 `pure-sasl`：

```python
# 在 app/main.py 或启动脚本中添加
import os
os.environ['THRIFT_SASL_PURE_SASL'] = '1'
```

或者在运行前设置环境变量：

```bash
export THRIFT_SASL_PURE_SASL=1
python -m app.main
```
