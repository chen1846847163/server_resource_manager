# 服务器资源管理系统 (SRM) 使用说明

## 1. 系统概述

本系统是一个**服务器资源管理系统 (Server Resource Manager, SRM)**，以 Web 方式提供统一的测试资源调度与测试任务管理能力。

**核心设计目标：**
- 测试人员无需关心用例在哪台机器上执行，系统自动调度
- 实时展示测试状态，呈现最终测试结果
- 与测试框架解耦，通过抽象层对接
- 支持服务器资源的临时禁用/启用，方便设备调试且不影响整体运行

**系统架构：**

```
                    ┌──────────────────────────────────┐
                    │        SRM Web Server (Flask)     │
                    │  ┌──────────┐  ┌───────────────┐  │
                    │  │ Web UI   │  │ REST API      │  │
                    │  │ (HTML/JS)│  │ (JSON)        │  │
                    │  └──────────┘  └──────┬────────┘  │
                    │                       │           │
                    │  ┌────────────────────▼─────────┐ │
                    │  │       任务调度器 (Scheduler)  │ │
                    │  └───────┬──────────┬───────────┘ │
                    │          │          │              │
                    │  ┌───────▼───┐ ┌────▼──────┐      │
                    │  │ 测试框架   │ │ 服务器资源 │      │
                    │  │ 抽象层     │ │ 池管理     │      │
                    │  └───────────┘ └───────────┘      │
                    └──────────────────────────────────┘
                         ▲                    ▲
            ┌────────────┘                    └────────────┐
            │                                             │
    ┌───────┴──────┐                            ┌────────┴───────┐
    │  CLI 客户端   │                            │   服务器资源    │
    │  (Python)    │                            │  server-01     │
    └──────────────┘                            │  server-02     │
                                                │  ...           │
                                                └────────────────┘
```

---

## 2. 快速启动

### 2.1 安装依赖

```bash
cd server_resource_manager
pip install -r requirements.txt
```

依赖项：
- `flask` — Web 框架
- `flask-cors` — 跨域支持
- `requests` — CLI 客户端 HTTP 请求

### 2.2 启动服务

```bash
# 默认启动 (监听 0.0.0.0:5000)
python app.py

# 自定义端口
SRM_PORT=8080 python app.py

# 自定义绑定地址
SRM_HOST=127.0.0.1 SRM_PORT=8080 python app.py
```

启动后控制台输出：
```
2026-04-08 ... [INFO] scheduler.scheduler: Scheduler started
2026-04-08 ... [INFO] root: Starting SRM server on 0.0.0.0:5000
 * Serving Flask app "app"
```

### 2.3 访问系统

浏览器打开 `http://localhost:5000`（或你配置的地址和端口）。

---

## 3. 使用方式一：Web 界面

系统提供四个主要页面，通过左侧导航栏切换。

### 3.1 仪表盘 (`/`)

系统首页，展示全局概览信息：

| 指标 | 说明 |
|------|------|
| 服务器总数 | 已注册的服务器数量 |
| 在线可用 | 状态为 online 且已启用的服务器数量 |
| 已禁用 | 被手动禁用的服务器数量 |
| 测试用例 | 已导入的测试用例总数 |
| 待执行任务 | 状态为 pending 的任务数 |
| 执行中 | 状态为 running 的任务数 |
| 已完成 | 全部用例通过的任务数 |
| 失败 | 存在失败用例的任务数 |

页面每 5 秒自动刷新，同时显示最近 10 条任务记录。

### 3.2 服务器管理 (`/servers`)

**添加服务器：**

1. 点击右上角「添加服务器」按钮
2. 填写表单：

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| 服务器名称 | 是 | 便于识别的名称 | `server-01` |
| 主机地址 | 是 | IP 或域名 | `192.168.1.101` |
| 端口 | 否 | 默认 22 | `22` |
| 标签 | 否 | 逗号分隔的标签 | `linux,arm` |

3. 点击「提交」

**禁用/启用服务器：**

点击服务器行右侧的「禁用」或「启用」按钮。禁用后：
- 该服务器**不会**被调度器分配新任务
- 已在该服务器上运行的任务**不受影响**
- 适合设备调试时临时隔离，不影响其他任务正常调度

**删除服务器：**

点击「删除」按钮并确认。删除前建议确保该服务器上没有正在运行的任务。

### 3.3 测试用例管理 (`/test-cases`)

**导入方式：**

| 方式 | 操作 | 说明 |
|------|------|------|
| 导入 Mock 用例 | 点击「导入 Mock 用例」 | 一键导入 6 个内置 Mock 测试用例，用于体验和验证系统 |
| 导入 JSON | 点击「导入 JSON」 | 将 JSON 数组粘贴到文本框中导入自定义用例 |
| 添加用例 | 点击「添加用例」 | 手动逐条添加 |

**JSON 导入格式：**

```json
[
  {
    "name": "test_example",
    "module": "demo",
    "description": "示例测试用例",
    "params": {
      "key": "value"
    }
  },
  {
    "name": "test_another",
    "module": "network",
    "description": "另一个测试",
    "params": {}
  }
]
```

字段说明：
- `name` (必填): 用例名称，如 `test_network_connectivity`
- `module` (可选): 所属模块，如 `network`、`hardware`
- `description` (可选): 用例描述
- `params` (可选): 测试参数，JSON 对象

**当前内置的 6 个 Mock 用例：**

| 名称 | 模块 | 说明 |
|------|------|------|
| `test_network_connectivity` | network | 网络连通性测试 |
| `test_disk_io` | hardware | 磁盘读写测试 |
| `test_cpu_stress` | hardware | CPU 压力测试 |
| `test_memory_leak` | memory | 内存泄漏测试 |
| `test_api_response` | api | API 响应时间测试 |
| `test_service_restart` | service | 服务重启行为测试 |

### 3.4 任务管理 (`/tasks`)

**创建测试任务：**

1. 点击「创建任务」
2. 填写任务名称（如 `smoke-test-1`）
3. 勾选要执行的测试用例（至少选一个）
4. 点击「提交」

任务创建后进入 `pending` 状态，调度器会在 3 秒内自动将其分配到可用服务器执行。

**任务状态流转：**

```
 pending  ──→  running  ──→  completed (全部通过)
                     │
                     └──→  failed (存在失败)

 pending/running  ──→  cancelled (手动取消)
```

| 状态 | 含义 |
|------|------|
| `pending` | 已创建，等待调度器分配服务器 |
| `running` | 正在某台服务器上执行 |
| `completed` | 执行完毕，所有用例通过 |
| `failed` | 执行完毕，存在失败用例 |
| `cancelled` | 被用户手动取消 |

**查看任务结果：**

点击任务行的「查看」按钮，弹出结果详情：

```
摘要信息：
  总计: 3 | 通过: 2 | 失败: 1

每个用例的执行结果：
  ✓ test_network_connectivity @ server-01 (970.7ms)
  ✗ test_disk_io @ server-01 (3160.4ms)
       Error: Unexpected response
  ✓ test_cpu_stress @ server-01 (720.6ms)
```

页面每 5 秒自动刷新任务列表。

**取消任务：**

对处于 `pending` 或 `running` 状态的任务，点击「取消」按钮。

---

## 4. 使用方式二：CLI 命令行

CLI 客户端位于 `cli/client.py`，用于通过命令行与 SRM 服务交互。

> 使用前需确保 SRM 服务已启动。

### 4.1 查看帮助

```bash
python cli/client.py --help
```

### 4.2 查看服务器列表

```bash
python cli/client.py servers
```

输出示例：
```
  [#1] server-01 (192.168.1.101:22)  status=online  enabled
  [#2] server-02 (192.168.1.102:22)  status=online  DISABLED
```

### 4.3 导入测试用例

准备 JSON 文件（如 `cases.json`）：
```json
[
  {"name": "test_login", "module": "auth", "description": "登录测试"},
  {"name": "test_logout", "module": "auth", "description": "登出测试"}
]
```

执行导入：
```bash
python cli/client.py import cases.json
```

输出示例：
```
Imported 2 test cases, ids=[1, 2]
```

### 4.4 提交测试任务

```bash
python cli/client.py submit --name "smoke-test" --case-ids 1,2,3
```

- `--name`: 任务名称（必填）
- `--case-ids`: 逗号分隔的测试用例 ID（必填）

输出示例：
```
Task created: id=1, message=Task created, waiting to be scheduled
```

### 4.5 查看任务列表

```bash
python cli/client.py tasks
```

输出示例：
```
  [#1] smoke-test  status=completed  server=server-01  created=2026-04-08 21:52:11
  [#2] full-regression  status=pending  server=auto  created=2026-04-08 21:55:00
```

### 4.6 查看任务结果

```bash
python cli/client.py result 1
```

输出示例：
```
Task #1: smoke-test
Status: failed
Result: 2/3 passed
  [PASS] test_network_connectivity @ server-01 (970.7ms)
  [FAIL] test_disk_io @ server-01 (3160.4ms)
       Error: Unexpected response
  [PASS] test_cpu_stress @ server-01 (720.6ms)
```

---

## 5. REST API 参考

所有 API 以 `/api` 为前缀，请求和响应均为 JSON 格式。

### 5.1 仪表盘

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dashboard/` | 获取全局统计信息 |

响应示例：
```json
{
  "servers": {"total": 3, "online": 2, "disabled": 1},
  "tasks": {"pending": 1, "running": 0, "completed": 5, "failed": 2, "cancelled": 0},
  "test_cases": 12
}
```

### 5.2 服务器管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/servers/` | 列出所有服务器 |
| GET | `/api/servers/?enabled_only=1` | 仅列出已启用的服务器 |
| GET | `/api/servers/<id>` | 获取单个服务器详情 |
| POST | `/api/servers/` | 添加服务器 |
| PUT | `/api/servers/<id>` | 更新服务器信息 |
| POST | `/api/servers/<id>/toggle` | 切换启用/禁用状态 |
| DELETE | `/api/servers/<id>` | 删除服务器 |

**添加服务器请求体：**
```json
{"name": "server-01", "host": "192.168.1.101", "port": 22, "tags": "linux,arm"}
```

**更新服务器请求体：**（仅传需要更新的字段）
```json
{"status": "offline", "tags": "linux,arm,debug"}
```

### 5.3 测试用例

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/test-cases/` | 列出所有测试用例 |
| GET | `/api/test-cases/<id>` | 获取单个用例详情 |
| POST | `/api/test-cases/import` | 从 JSON 数组批量导入用例 |
| POST | `/api/test-cases/import-mock` | 一键导入 Mock 用例 |
| DELETE | `/api/test-cases/<id>` | 删除用例 |

**批量导入请求体：**
```json
[
  {"name": "test_xxx", "module": "mod", "description": "...", "params": {}}
]
```

### 5.4 任务管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tasks/` | 列出所有任务 |
| GET | `/api/tasks/<id>` | 获取任务详情（含结果） |
| POST | `/api/tasks/` | 创建任务 |
| POST | `/api/tasks/<id>/cancel` | 取消任务 |
| DELETE | `/api/tasks/<id>` | 删除任务 |

**创建任务请求体：**
```json
{"name": "smoke-test", "test_case_ids": [1, 2, 3]}
```

**任务详情响应（含结果）：**
```json
{
  "id": 1,
  "name": "smoke-test",
  "status": "completed",
  "server_name": "server-01",
  "test_case_ids": [1, 2, 3],
  "result": {
    "summary": {"total": 3, "passed": 3, "failed": 0},
    "details": [
      {
        "test_case": "test_network_connectivity",
        "server": "server-01",
        "passed": true,
        "duration_ms": 970.7,
        "error": null,
        "output": "Mock output for ..."
      }
    ]
  },
  "created_at": "2026-04-08 21:52:11",
  "started_at": "2026-04-08T21:52:11.955607",
  "finished_at": "2026-04-08T21:52:15.297331"
}
```

---

## 6. 调度器工作原理

调度器在服务启动时自动运行，每 **3 秒** 轮询一次：

1. 查询所有 `pending` 状态的任务
2. 查询所有可用服务器（`enabled=1` 且 `status=online`）
3. 优先将任务分配给**当前没有正在执行任务的空闲服务器**
4. 若所有可用服务器都在忙，则分配给第一个可用服务器（排队）
5. 若无可用服务器，任务保持 `pending`，日志打印警告
6. 任务执行在独立线程中，不阻塞调度器

**任务结果判定：**
- 全部用例通过 → `completed`
- 任一用例失败 → `failed`

---

## 7. 环境变量配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SRM_HOST` | `0.0.0.0` | 服务绑定地址 |
| `SRM_PORT` | `5000` | 服务监听端口 |
| `SRM_DEBUG` | `true` | 是否开启调试模式 |

---

## 8. 项目目录结构

```
server_resource_manager/
├── app.py                     # 应用主入口
├── config.py                  # 全局配置
├── requirements.txt           # Python 依赖
├── doc/
│   └── USAGE.md               # 本文档
├── data/                      # 运行时数据（自动创建）
│   ├── srm.db                 # SQLite 数据库
│   └── uploads/               # 上传文件目录
├── models/
│   ├── database.py            # 数据库初始化与连接管理
│   ├── server.py              # 服务器资源 CRUD
│   └── task.py                # 测试用例 & 任务 CRUD
├── api/
│   ├── servers.py             # 服务器管理 REST API
│   └── tasks.py               # 用例/任务/仪表盘 REST API
├── scheduler/
│   └── scheduler.py           # 后台任务调度器
├── mock/
│   └── mock_test_runner.py    # Mock 测试执行器（Demo 用）
├── cli/
│   └── client.py              # 命令行客户端
├── templates/                 # Jinja2 HTML 模板
│   ├── base.html
│   ├── dashboard.html
│   ├── servers.html
│   ├── test_cases.html
│   └── tasks.html
└── static/                    # 前端静态资源
    ├── css/style.css
    └── js/app.js
```

---

## 9. 当前 Demo 限制与后续扩展方向

### 当前 Demo 的 Mock 层

`mock/mock_test_runner.py` 中的 `run_mock_test()` 函数模拟了测试执行：
- 随机等待 0.5~2 秒模拟执行耗时
- 70%~100% 的概率返回通过
- 生成随机的执行时长和错误信息

### 如何对接真实测试框架

替换 `scheduler/scheduler.py` 中的 `_execute_task` 函数即可：

```python
# 当前调用的是 mock 层
from mock.mock_test_runner import run_mock_test

# 替换为真实测试框架，例如：
# from your_test_framework import run_test
# r = run_test(tc["name"], server, tc.get("params"))
```

只需确保 `run_test` 函数返回相同格式的结果字典：
```python
{
    "test_case": str,       # 用例名称
    "server": str,          # 执行服务器名
    "server_host": str,     # 服务器地址
    "passed": bool,         # 是否通过
    "duration_ms": float,   # 执行耗时（毫秒）
    "error": str | None,    # 错误信息（通过时为 None）
    "output": str,          # 标准输出
}
```

### 建议的后续扩展

| 方向 | 说明 |
|------|------|
| 真实测试框架对接 | 实现 `run_test()` 替换 Mock 层 |
| 服务器心跳检测 | 定时 ping 检查服务器真实在线状态，自动更新 status |
| 用户认证 | 添加登录/权限管理 |
| 任务优先级 | 支持任务优先级排序 |
| 并发控制 | 每台服务器限制最大并发任务数 |
| 结果导出 | 支持 HTML/PDF 测试报告导出 |
| WebSocket 推送 | 实时推送任务状态变化，替代轮询 |
| 数据持久化升级 | 迁移到 MySQL/PostgreSQL |
| 用例文件上传 | 支持上传 Python 测试脚本文件 |
