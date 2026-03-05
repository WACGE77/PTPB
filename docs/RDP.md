【通用开发要求】
1. 适配体系：基于现有Vue3+TS前端、Python/Django后端的运维堡垒机架构，集成RDP功能
2. 核心技术：采用Apache Guacamole实现RDP协议解析与Web化远程桌面
3. 适配要求：无缝对接现有RBAC权限、资源管理、审计日志模块，遵循原有代码规范
4. 网关适配：保证Traefik可识别并转发RDP相关的WebSocket请求与API接口

【后端开发指引】
1. 模块扩展：在现有resource资源模块下新增rdp子模块，遵循原有目录结构规范
2. 数据模型：设计RDP配置模型，关联服务器资源、凭证表，包含rdp_port、resolution、color_depth、enable_clipboard字段
3. 接口开发：封装Guacamole API，开发/resource/rdp/connection/接口，返回JWT令牌、WebSocket地址、RDP配置，加入RBAC权限校验
4. 审计扩展：新增RDP审计日志模型，记录resource_id、session_id、connect_time、disconnect_time、operation_type、error_msg，连接/断开/异常时自动落库
5. 服务部署：部署Guacamole Server，配置guacd服务，保证与后端网络互通，处理RDP协议代理
6. 路由配置：新增RDP路由挂载至/resource/rdp路径，适配Traefik路由匹配规则

【前端开发指引】
1. 目录扩展：在api、components、struct、utils、views目录新增RDP相关文件，遵循原有命名规范
2. 核心组件：基于guacamole-common-js开发RdpTerminal组件，实现WebSocket连接、RDP桌面渲染、键鼠交互
3. 状态管理：封装RDP连接状态（disconnected/connecting/connected/error），展示异常提示
4. 配置组件：开发RdpConfig组件，支持RDP参数展示与修改，同步至后端配置
5. 类型定义：新增RDP相关TS类型（RDPResource、RDPConnectionParams、RDPStatus）
6. API封装：开发getRDPConnectionParams、recordRDPAuditLog接口，携带原有认证token
7. 路由配置：新增/rdp/:resourceId路由，加入登录/权限守卫，适配Traefik路径转发
8. 工具函数：封装Guacamole初始化、断开、窗口自适应、断网重连逻辑

【Traefik网关配置指引】
1. 路由规则：配置/guacamole/websocket路径转发至Guacamole服务，启用WebSocket支持
2. API转发：配置/resource/rdp路径转发至堡垒机后端服务
3. 适配要求：沿用现有认证中间件，保证请求路由无异常，与现有网关配置兼容

【集成联调要求】
1. 权限联动：实现“用户-角色-权限-RDP资源”的权限管控，未授权用户无法访问
2. 日志统一：RDP审计日志在原有审计页面展示，与现有日志体系统一
3. 异常处理：覆盖权限不足、资源不可达、断网、令牌过期等场景，给出友好提示
4. 兼容性：支持Chrome/Firefox/Edge浏览器，适配不同屏幕尺寸