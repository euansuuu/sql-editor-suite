# SQL Editor Suite - Ubuntu 部署指南

## 📋 前置条件

| 软件 | 版本要求 |
|------|---------|
| Ubuntu | 20.04 LTS 或更高版本（推荐 22.04 / 24.04） |
| Python | 3.10 - 3.12（推荐 3.12） |
| Git | 最新版本 |
| Node.js | 18+（用于前端） |

---

## 🔧 第一步：安装系统依赖

### 1. 更新系统并安装基础编译工具

```bash
sudo apt-get update && sudo apt-get upgrade -y

# 安装编译工具链
sudo apt-get install -y \
  build-essential \
  gcc \
  g++ \
  make \
  cmake \
  pkg-config
```

### 2. 安装 SASL 和 Kerberos 开发库（Hive/Trino 必需）

```bash
sudo apt-get install -y \
  libsasl2-dev \
  libsasl2-modules-gssapi-mit \
  libkrb5-dev \
  krb5-user \
  libssl-dev
```

### 3. 安装 Python 开发库

```bash
# Python 3.12（如果系统自带则跳过）
sudo apt-get install -y \
  python3-dev \
  python3-pip \
  python3-venv
```

---

## 🐍 第二步：准备 Python 环境

### 1. 克隆项目

```bash
git clone https://github.com/euansuuu/sql-editor-suite.git
cd sql-editor-suite
```

### 2. 创建虚拟环境

```bash
cd sql-editor-backend

# 使用 venv
python3 -m venv .venv
source .venv/bin/activate

# 或者使用 uv（推荐，更快）
# pip install uv
# uv venv
# source .venv/bin/activate
```

---

## ⚙️ 第三步：安装后端依赖

### ⚠️ 重要说明：Python 3.12 兼容性问题

`sasl==0.3.1` 包与 Python 3.12 不兼容（C++ 扩展依赖已移除的 `longintrepr.h` 头文件）。

本项目已修复，改用纯 Python 实现的 `pure-sasl==0.6.2`。

### 安装依赖

```bash
# 确保在虚拟环境中
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 或者使用 uv
# uv pip install -r requirements.txt
```

### ✅ 验证安装

```bash
python -c "
# 验证 Python 3.12 兼容性
import os
os.environ['THRIFT_SASL_PURE_SASL'] = '1'

# 测试所有关键包导入
from pyhive import hive
from pyhive import presto
from TCLIService import ttypes
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from fastapi import FastAPI
from pydantic import BaseModel
import sqlalchemy

print('✅ All dependencies installed successfully!')
print('✅ Python 3.12 compatibility verified')
print('✅ pure-sasl enabled')
"
```

---

## 🚀 第四步：启动后端服务

### 1. 基础配置（可选，修改配置文件）

```bash
# 查看配置
cat config/settings.py

# 如有需要，创建 .env 文件
cp .env.example .env
# 编辑 .env 修改配置
```

### 2. 启动服务

```bash
# 确保在虚拟环境中
source .venv/bin/activate

# 启动服务
python -m app.main
```

### 3. 验证启动

服务启动后，访问以下地址验证：

- **Swagger API 文档**：http://localhost:8000/docs
- **Redoc 文档**：http://localhost:8000/redoc
- **健康检查**：http://localhost:8000/health

---

## 🌐 第五步：前端部署（Vue 3）

### 1. 安装 Node.js（如未安装）

```bash
# 方法一：使用 NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证
node --version  # >= 18.x
npm --version
```

### 2. 安装前端依赖

```bash
cd ../vue-sql-editor-v3

# 安装依赖
npm install

# 或者使用 pnpm（更快）
# npm install -g pnpm
# pnpm install
```

### 3. 配置 API 地址

编辑 `vite.config.ts` 或 `.env` 文件，修改后端 API 地址：

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // 后端地址
        changeOrigin: true
      }
    }
  }
})
```

### 4. 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:5173

### 5. 生产环境构建

```bash
npm run build

# 构建产物在 dist/ 目录
# 可使用 nginx 部署
```

---

## 📝 完整一键安装脚本（推荐）

```bash
#!/bin/bash
# SQL Editor Suite - Ubuntu 一键安装脚本

set -e

echo "🚀 开始部署 SQL Editor Suite..."

# 1. 安装系统依赖
echo "📦 安装系统依赖..."
sudo apt-get update
sudo apt-get install -y build-essential gcc g++ make cmake pkg-config \
  libsasl2-dev libsasl2-modules-gssapi-mit libkrb5-dev krb5-user libssl-dev \
  python3-dev python3-pip python3-venv git

# 2. 克隆项目
echo "📥 克隆项目..."
git clone https://github.com/euansuuu/sql-editor-suite.git
cd sql-editor-suite

# 3. 后端安装
echo "🐍 配置后端环境..."
cd sql-editor-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. 验证后端
echo "✅ 验证后端依赖..."
python -c "
import os
os.environ['THRIFT_SASL_PURE_SASL'] = '1'
from pyhive import hive
from fastapi import FastAPI
from pydantic import BaseModel
import sqlalchemy
print('✅ 后端依赖验证通过')
"

echo "🎉 部署完成！"
echo ""
echo "启动后端："
echo "  cd sql-editor-backend && source .venv/bin/activate && python -m app.main"
echo ""
echo "访问："
echo "  API 文档：http://localhost:8000/docs"
echo ""
echo "前端部署请参考 vue-sql-editor-v3/README.md"
```

保存为 `install.sh`，然后执行：

```bash
chmod +x install.sh
./install.sh
```

---

## ❌ 常见问题与解决方案

### 问题 1：sasl 编译失败 - `longintrepr.h: No such file or directory`

**原因**：`sasl==0.3.1` 与 Python 3.12 不兼容。

**解决方案**（项目已修复）：

```bash
# 卸载有问题的包
pip uninstall -y sasl

# 安装 pure-sasl 替代
pip install pure-sasl==0.6.2
```

---

### 问题 2：thrift 版本冲突

**原因**：`impyla==0.18.0` 要求 `thrift==0.16.0`，与其他包冲突。

**解决方案**（项目已修复）：

```bash
pip install thrift==0.16.0
```

---

### 问题 3：`pyhive[hive]` 强制安装 sasl

**原因**：`pyhive[hive]` 的 extras 依赖强制安装 `sasl`。

**解决方案**（项目已修复）：

```bash
# 不要用 pyhive[hive]，改用 pyhive + pure-sasl
pip uninstall -y pyhive sasl
pip install pyhive==0.7.0 pure-sasl==0.6.2
```

---

### 问题 4：缺少编译工具

**错误**：`error: command 'c++' failed: No such file or directory`

**解决方案**：

```bash
sudo apt-get install -y build-essential g++
```

---

### 问题 5：SASL 相关错误

**错误**：`Could not start SASL: No mechanism available`

**解决方案**：

```bash
sudo apt-get install -y libsasl2-dev libsasl2-modules-gssapi-mit
```

---

### 问题 6：`from_attributes` / `orm_mode` 警告

**原因**：Pydantic V2 重命名了配置项。

**解决方案**（项目已修复）：

已将所有 `orm_mode = True` 改为 `from_attributes = True`。

---

### 问题 7：`cannot import name 'list' from 'typing'`

**原因**：Python 3.9+ 移除了 `typing.List/list` 的导入方式。

**解决方案**（项目已修复）：

```python
# 错误写法（Python 3.8 及之前）
from typing import List, Dict

# 正确写法（Python 3.9+ PEP 585）
list[str]
dict[str, int]
```

---

## 🔐 Kerberos 环境配置（可选）

如果需要连接 Kerberos 认证的 Hive/Impala：

### 1. 配置 krb5.conf

```bash
sudo nano /etc/krb5.conf
```

示例配置：

```ini
[libdefaults]
    default_realm = YOUR.COMPANY.COM
    dns_lookup_realm = false
    dns_lookup_kdc = false
    ticket_lifetime = 24h
    renew_lifetime = 7d
    forwardable = true

[realms]
    YOUR.COMPANY.COM = {
        kdc = kdc1.your.company.com
        admin_server = kdc1.your.company.com
    }

[domain_realm]
    .your.company.com = YOUR.COMPANY.COM
    your.company.com = YOUR.COMPANY.COM
```

### 2. 获取 Kerberos Ticket

```bash
# 使用 keytab
kinit -kt /path/to/your.keytab hive/host@YOUR.COMPANY.COM

# 或者使用密码
kinit your-principal@YOUR.COMPANY.COM

# 查看票据
klist
```

---

## 📊 系统要求总结

| 资源 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 10 GB | 20 GB+ |
| 系统 | Ubuntu 20.04+ | Ubuntu 22.04 LTS |

---

## 📚 参考文档

- 项目 GitHub：https://github.com/euansuuu/sql-editor-suite
- 后端 README：sql-editor-backend/README.md
- 前端 README：vue-sql-editor-v3/README.md
- FastAPI 文档：https://fastapi.tiangolo.com/
- Vue 3 文档：https://vuejs.org/

---

**如有问题，请提交 Issue 或查看项目 README！** 🎉
