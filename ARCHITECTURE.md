# 项目架构说明

下面是基于当前仓库文件结构为 `PTPB` 项目绘制的架构图（Mermaid）。图中仅包含能从源码直接确认的组件和关联系统。

简要说明：项目为 Django 项目（`BackEnd` 为项目配置），包含多个应用（`audit`、`perm`、`rbac`、`resource`、`terminal` 等）。`BackEnd/asgi.py` 支持 WebSocket（`terminal/consumers.py`），`manage.py` 可加载 `default-data.json` 作为 fixtures。
# 项目架构说明

下面是基于仓库代码绘制的系统级架构图（以堡垒机/Bastion 主体为中心）。图中描述了主要运行时组件、数据流与关键模型职责：鉴权（JWT）、RBAC/权限、资源与凭证、终端代理（WebSocket -> SSH）、以及审计记录。

```mermaid
flowchart LR
  subgraph Actors
    Browser[用户浏览器 / Web UI]
    APIClient[API 客户端 / CLI]
  end

  subgraph Edge[接入层]
    direction TB
    Nginx[NGINX / 反向代理 (可选)]
    WSGI[WSGI 接口 (BackEnd/wsgi.py)]
    ASGI[ASGI / WebSocket (BackEnd/asgi.py)]
  end

  Browser -->|HTTP REST / GraphQL| Nginx
  APIClient -->|HTTP API| Nginx
  Nginx --> WSGI
  Browser -->|WebSocket (终端)| ASGI

  subgraph App[堡垒机应用 (BackEnd)]
    direction TB
    WebAPI[REST API (DRF)]
    Auth[鉴权模块 (perm.authentication - JWT)]
    RBAC[RBAC 模型 (rbac.models: User/Role/Permission)]
    PermEngine[权限引擎 (perm.models / perm.utils)]
    ResourceSvc[资源管理 (resource.models: Resource/Voucher)]
    TerminalSvc[终端代理 (terminal.consumers / protocol.py)]
    AuditSvc[审计记录 (audit.models / Logging)]
    DB[(数据库)]
  end

  WSGI --> WebAPI
  WebAPI --> Auth
  WebAPI --> RBAC
  WebAPI --> ResourceSvc
  WebAPI --> AuditSvc
  WebAPI --> DB

  ASGI --> TerminalSvc
  TerminalSvc --> Auth
  TerminalSvc --> PermEngine
  TerminalSvc --> ResourceSvc
  TerminalSvc --> AuditSvc
  TerminalSvc --> DB

  Auth --> RBAC
  PermEngine --> RBAC
  ResourceSvc --> DB
  AuditSvc --> DB

  subgraph Target[被管理主机]
    direction TB
    Host[目标主机 (SSH/Telnet/等)]
  end

  TerminalSvc -->|SSH (paramiko / asyncssh)| Host

  %% token / session flow
  Browser -.->|登录获取 JWT| Auth
  Auth -.->|返回 AccessToken| Browser
  Browser -.->|在 WebSocket 握手/消息中携带 token| TerminalSvc

  %% permission checks
  PermEngine -.->|检查 role/base/resource/voucher 权限| ResourceSvc

  %% audit
  AuditSvc -.->|记录 Login/Session/操作| DB

  classDef svc fill:#f9f,stroke:#333,stroke-width:1px
  class WebAPI,Auth,PermEngine,ResourceSvc,TerminalSvc,AuditSvc svc
```

关键职责说明：
- **鉴权 (perm.authentication)**: 使用 JWT（simplejwt），为 REST 接口与 WebSocket 连接提供用户身份验证（见 `perm/authentication.py`）。
- **权限与角色 (rbac、perm.models)**: `rbac.models` 定义 `User/Role/Permission`，`perm.models` 定义 `BaseAuth/ResourceAuth/ResourceVoucherAuth`，用于实现全局/资源粒度权限检查。
- **资源管理 (resource.models)**: `Resource`、`ResourceVoucher` 存储目标主机地址、端口及登录凭证。
- **终端代理 (terminal/consumers.py, protocol.py)**: `SSHConsumer` 接收 WebSocket 请求，验证 token 与权限后，使用 `AsyncSSHClient`（`asyncssh`/`paramiko`） 创建到目标主机的 SSH 会话并做数据转发，同时调用 `audit.Logging` 记录会话。
- **审计 (audit.models, audit.Logging)**: 记录登录、会话开始/结束、以及命令/操作记录（SessionLog、OperationLog、ShellOperationLog 等）。

如何查看与导出：
- 在 VS Code 中使用 `Mermaid Markdown Preview` 插件直接渲染 `ARCHITECTURE.md`。
- 如需我把该 Mermaid 渲染为 PNG 或 SVG 并提交为文件，我可以生成并添加到仓库。
