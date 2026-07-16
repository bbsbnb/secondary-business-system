# 天行建筑智能管理平台 - 部署与运维手册

## 项目概述

天行建筑智能管理平台是一个基于 FastAPI + Vue 3 的全流程工程管理平台，支持 25 个业务节点（M1-M25）、审批流引擎、预警中心、文档管理等核心功能。

---

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端 | Python + FastAPI | 3.11.15 + 0.115.0 |
| 数据库 | PostgreSQL / SQLite | 17 / latest |
| 缓存 | Redis | 7-alpine |
| 对象存储 | MinIO | latest |
| 任务队列 | Celery | 5.4.0 |
| 前端 | Vue 3 + TypeScript + Element Plus | 3.4 + 5.4 + 2.7 |
| 构建 | Vite | 5.3 |

---

## 环境要求

- **操作系统**: Windows 10/11 或 Linux (Ubuntu/CentOS)
- **Python**: 3.11+
- **Node.js**: 18+ (推荐 20+)
- **PostgreSQL**: 16+ (生产环境)
- **Redis**: 7+
- **MinIO**: latest (可选，用于文件存储)
- **Docker**: 20+ (可选，用于一键部署)

---

## 快速启动（本地开发）

### 1. 启动 PostgreSQL

#### Windows:
```bash
# PostgreSQL 17 已安装，服务名为 postgresql-x64-17
net start postgresql-x64-17
```

#### Linux:
```bash
sudo systemctl start postgresql
```

### 2. 创建数据库

```bash
# 使用 Administrator 用户（Windows 安装时自动创建）
createdb -U Administrator tianxing

# 或使用 psql
psql -U Administrator -d template1 -c "CREATE DATABASE tianxing;"
```

### 3. 初始化数据库表和数据

```bash
cd backend
python init_db.py
```

输出示例：
```
📦 创建数据库表...
✅ 数据库表创建完成
  ✅ 部门: 项目部
  ✅ 部门: 工程部
  ...
🎉 数据库初始化完成！

📋 登录信息:
   管理员: admin / admin123
   测试用户:
     zhangsan / project123
     lisi / project123
```

### 4. 启动后端服务

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 Swagger UI: http://localhost:8000/docs

### 5. 启动前端服务

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run dev
```

访问前端: http://localhost:3000

---

## Docker 一键部署

### 1. 安装 Docker

```bash
# Ubuntu
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# CentOS
sudo yum install -y docker-ce
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. 启动所有服务

```bash
cd /path/to/天行建筑-全流程系统
docker-compose up -d
```

这将启动以下服务：
- PostgreSQL:5432
- Redis:6379
- MinIO:9000 (API) / 9001 (Console)
- Backend:8000
- Frontend:3000

### 3. 查看日志

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 4. 停止服务

```bash
docker-compose down
```

---

## API 端点概览

| 模块 | 路径 | 方法 | 说明 |
|------|------|------|------|
| 认证 | `/api/v1/auth/login` | POST | 用户登录 |
| 认证 | `/api/v1/auth/me` | GET | 获取当前用户 |
| 项目 | `/api/v1/projects` | GET/POST | 项目列表/创建 |
| 部门 | `/api/v1/departments` | GET | 部门列表 |
| 权限 | `/api/v1/permissions/matrix` | GET | 权限矩阵 |
| 基线 | `/api/v1/baseline/{project_id}` | GET/POST | 基线数据 |
| 审批 | `/api/v1/approval/instances` | POST | 创建审批实例 |
| 审批 | `/api/v1/approval/my-pending` | GET | 我的待办 |
| M6 | `/api/v1/m6/price` | POST | 认质认价 |
| M7 | `/api/v1/m7/contact` | POST | 工作联系单 |
| M8 | `/api/v1/m8/visa` | POST | 签证执行 |
| M9 | `/api/v1/m9/claim` | POST | 索赔执行 |
| M10 | `/api/v1/m10/change` | POST | 设计变更 |
| M11 | `/api/v1/m11/verification` | POST | 月验工计价 |
| M12 | `/api/v1/m12/material` | POST | 材料结算 |
| M13 | `/api/v1/m13/consumption` | POST | 消耗核定 |
| M24 | `/api/v1/contracts` | POST | 建造合同 |
| 文档 | `/api/v1/documents` | GET/POST | 资料库 |
| 预警 | `/api/v1/alerts` | GET | 预警列表 |
| 移动端 | `/api/v1/mobile/approvals` | GET | 移动端审批 |

完整 API 文档: http://localhost:8000/docs

---

## 配置说明

### 环境变量

在 `backend/.env` 文件中配置：

```env
DATABASE_URL=postgresql://Administrator@localhost:5432/tianxing
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
SECRET_KEY=tianxing-secret-key-change-in-production
DEBUG=True
```

### 数据库连接

- **生产环境**: 使用 PostgreSQL
- **开发环境**: 可使用 SQLite（修改 `config.py` 中的 `DATABASE_URL`）

---

## 常见问题

### 1. SQLAlchemy 表注册冲突

**错误**: `InvalidRequestError: Table 'projects' is already defined`

**原因**: `from app.models.__init__ import X` 导致模块重复加载

**解决**: 统一使用 `from app.models import X`

### 2. bcrypt 兼容性问题

**错误**: `module 'bcrypt' has no attribute '__about__'`

**解决**: 安装兼容版本 `pip install bcrypt==4.0.1`

### 3. 前端构建失败

**错误**: `"docApi" is not exported by "src/api/index.ts"`

**解决**: 将 `docApi` 改为 `documentApi`

### 4. PostgreSQL 连接失败

**错误**: `connection to server at "localhost" (::1), port 5432 failed`

**解决**: 
- Windows: `net start postgresql-x64-17`
- Linux: `sudo systemctl start postgresql`
- 检查 `pg_hba.conf` 和 `postgresql.conf` 配置

---

## 运维指南

### 备份数据库

```bash
# PostgreSQL 备份
pg_dump -U Administrator tianxing > backup_$(date +%Y%m%d).sql

# 恢复
psql -U Administrator tianxing < backup_20260716.sql
```

### 监控服务状态

```bash
# Docker 容器状态
docker-compose ps

# 后端健康检查
curl http://localhost:8000/api/v1/health

# 前端健康检查
curl http://localhost:3000
```

### 更新代码

```bash
# 后端
git pull
pip install -r requirements.txt
python init_db.py  # 如果有新表需要创建

# 前端
git pull
npm install
npm run build
```

---

## 安全建议

1. **修改默认密码**: 立即修改 `admin` 用户的默认密码
2. **配置 HTTPS**: 生产环境必须启用 TLS/SSL
3. **限制数据库访问**: 仅允许应用服务器 IP 连接数据库
4. **定期备份**: 设置定时任务自动备份数据库
5. **更新依赖**: 定期检查并更新安全漏洞

---

## 联系方式

- 技术支持: [REDACTED]
- 问题反馈: [REDACTED]

---

*文档版本: v1.0*
*最后更新: 2026-07-16*
