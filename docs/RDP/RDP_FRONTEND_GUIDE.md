# RDP 前端对接指南

## 1. 概述

本文档详细介绍如何在前端对接RDP（Remote Desktop Protocol）远程桌面功能，包括WebSocket连接建立、参数配置、消息格式和错误处理等内容。

## 2. 技术栈

- **前端框架**: 支持WebSocket的任何前端框架（Vue、React、Angular等）
- **WebSocket**: 用于与后端建立实时连接
- **Guacamole客户端**: 用于处理RDP协议数据

## 3. 连接流程

### 3.1 前置条件

1. 用户已登录系统，获取到有效的JWT令牌
2. 前端已获取到目标Windows服务器的资源ID和凭证ID
3. Guacamole服务器已部署并运行

### 3.2 连接步骤

1. 构建WebSocket连接URL
2. 建立WebSocket连接
3. 发送初始化消息（如窗口大小调整）
4. 处理接收到的RDP数据
5. 发送用户输入数据
6. 关闭连接

## 4. WebSocket连接

### 4.1 连接URL

```
ws://设备/api/terminal/rdp/?token=<access_token>&resource_id=<resource_id>&voucher_id=<voucher_id>&resolution=<resolution>&color_depth=<color_depth>&enable_clipboard=<enable_clipboard>
```

### 4.2 参数说明

| 参数 | 是否必须 | 类型 | 默认值 | 说明 |
|------|---------|------|--------|------|
| token | 是 | 字符串 | - | JWT访问令牌 |
| resource_id | 是 | 整数 | - | Windows服务器资源ID |
| voucher_id | 是 | 整数 | - | 登录凭证ID |
| resolution | 否 | 字符串 | 1024x768 | 分辨率 |
| color_depth | 否 | 整数 | 16 | 颜色深度 |
| enable_clipboard | 否 | 布尔值 | true | 是否启用剪贴板 |

### 4.3 示例连接URL

```
ws://192.168.1.100/api/terminal/rdp/?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...&resource_id=1&voucher_id=1&resolution=1920x1080&color_depth=24&enable_clipboard=true
```

## 5. 消息格式

### 5.1 客户端 → 服务器

#### 5.1.1 调整窗口大小

```json
{
    "type": 1,
    "data": {
        "cols": 1920,
        "rows": 1080
    }
}
```

#### 5.1.2 发送RDP数据

```json
{
    "type": 2,
    "data": "<Guacamole协议数据>"
}
```

### 5.2 服务器 → 客户端

- 服务器直接发送Guacamole协议数据，前端需要使用Guacamole客户端库进行解析和渲染

## 6. Guacamole客户端集成

### 6.1 安装Guacamole客户端

```bash
# 使用npm安装
npm install guacamole-common-js

# 或使用yarn
 yarn add guacamole-common-js
```

### 6.2 基本使用示例

```javascript
import Guacamole from 'guacamole-common-js';

// 创建WebSocket连接
const ws = new WebSocket('ws://设备/api/terminal/rdp/?token=...&resource_id=1&voucher_id=1');

// 创建Guacamole客户端
const client = new Guacamole.Client(ws);

// 获取显示元素
const display = document.getElementById('rdp-display');

// 附加显示到DOM
client.getDisplay().attach(display);

// 处理键盘事件
const keyboard = client.getKeyboard();
document.addEventListener('keydown', (e) => {
    keyboard.handleKeydown(e);
});
document.addEventListener('keyup', (e) => {
    keyboard.handleKeyup(e);
});

// 处理鼠标事件
const mouse = client.getMouse();
display.addEventListener('mousedown', (e) => {
    mouse.handleMouseDown(e);
});
display.addEventListener('mousemove', (e) => {
    mouse.handleMouseMove(e);
});
display.addEventListener('mouseup', (e) => {
    mouse.handleMouseUp(e);
});
display.addEventListener('wheel', (e) => {
    mouse.handleWheel(e);
});

// 调整显示大小
function resizeDisplay() {
    const width = display.clientWidth;
    const height = display.clientHeight;
    client.getDisplay().resize(width, height);
    
    // 发送窗口大小调整消息
    ws.send(JSON.stringify({
        type: 1,
        data: {
            cols: width,
            rows: height
        }
    }));
}

// 初始调整大小
resizeDisplay();

// 窗口大小变化时调整
window.addEventListener('resize', resizeDisplay);

// 关闭连接
function closeConnection() {
    ws.close();
}
```

## 7. 错误处理

### 7.1 WebSocket错误

```javascript
ws.addEventListener('error', (error) => {
    console.error('WebSocket连接错误:', error);
    // 显示错误消息给用户
    showError('无法连接到远程服务器，请检查网络连接');
});

ws.addEventListener('close', (event) => {
    if (event.code !== 1000) {
        console.error('WebSocket连接异常关闭:', event.code, event.reason);
        // 显示错误消息给用户
        showError('远程连接已关闭: ' + event.reason);
    } else {
        console.log('WebSocket连接正常关闭');
    }
});
```

### 7.2 连接超时处理

```javascript
// 设置连接超时
let connectionTimeout = setTimeout(() => {
    console.error('连接超时');
    ws.close();
    showError('连接超时，请检查网络连接或服务器状态');
}, 10000); // 10秒超时

ws.addEventListener('open', () => {
    clearTimeout(connectionTimeout);
    console.log('WebSocket连接已建立');
});
```

## 8. 性能优化

### 8.1 带宽优化

- 根据网络状况调整分辨率和颜色深度
- 启用Guacamole的压缩功能
- 避免在网络不稳定时使用高分辨率

### 8.2 响应速度优化

- 使用WebWorker处理Guacamole协议解析
- 优化DOM操作，减少重排和重绘
- 使用requestAnimationFrame进行渲染

## 9. 安全考虑

### 9.1 令牌安全

- 不要在URL中明文传递令牌（虽然WebSocket URL会加密传输，但仍建议使用更安全的方式）
- 令牌应设置合理的过期时间
- 避免在前端存储令牌

### 9.2 数据安全

- 确保WebSocket连接使用WSS（WebSocket Secure）
- 对敏感操作进行额外的身份验证
- 定期检查连接状态，防止会话劫持

## 10. 完整示例

### 10.1 Vue组件示例

```vue
<template>
  <div class="rdp-container">
    <div class="rdp-header">
      <h3>远程桌面连接</h3>
      <button @click="disconnect" class="disconnect-btn">断开连接</button>
    </div>
    <div id="rdp-display" class="rdp-display"></div>
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script>
import Guacamole from 'guacamole-common-js';

export default {
  name: 'RdpComponent',
  props: {
    resourceId: {
      type: Number,
      required: true
    },
    voucherId: {
      type: Number,
      required: true
    },
    token: {
      type: String,
      required: true
    },
    resolution: {
      type: String,
      default: '1024x768'
    },
    colorDepth: {
      type: Number,
      default: 16
    },
    enableClipboard: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      ws: null,
      client: null,
      error: '',
      connectionTimeout: null
    };
  },
  mounted() {
    this.connect();
  },
  beforeUnmount() {
    this.disconnect();
  },
  methods: {
    connect() {
      const url = `ws://${window.location.host}/api/terminal/rdp/?token=${this.token}&resource_id=${this.resourceId}&voucher_id=${this.voucherId}&resolution=${this.resolution}&color_depth=${this.colorDepth}&enable_clipboard=${this.enableClipboard}`;
      
      this.ws = new WebSocket(url);
      
      // 设置连接超时
      this.connectionTimeout = setTimeout(() => {
        this.error = '连接超时，请检查网络连接或服务器状态';
        this.disconnect();
      }, 10000);
      
      this.ws.addEventListener('open', () => {
        clearTimeout(this.connectionTimeout);
        this.initGuacamole();
      });
      
      this.ws.addEventListener('error', (error) => {
        console.error('WebSocket错误:', error);
        this.error = '无法连接到远程服务器，请检查网络连接';
      });
      
      this.ws.addEventListener('close', (event) => {
        if (event.code !== 1000) {
          this.error = `远程连接已关闭: ${event.reason}`;
        }
      });
    },
    
    initGuacamole() {
      this.client = new Guacamole.Client(this.ws);
      
      const display = document.getElementById('rdp-display');
      this.client.getDisplay().attach(display);
      
      // 处理键盘事件
      const keyboard = this.client.getKeyboard();
      document.addEventListener('keydown', (e) => {
        keyboard.handleKeydown(e);
      });
      document.addEventListener('keyup', (e) => {
        keyboard.handleKeyup(e);
      });
      
      // 处理鼠标事件
      const mouse = this.client.getMouse();
      display.addEventListener('mousedown', (e) => {
        mouse.handleMouseDown(e);
      });
      display.addEventListener('mousemove', (e) => {
        mouse.handleMouseMove(e);
      });
      display.addEventListener('mouseup', (e) => {
        mouse.handleMouseUp(e);
      });
      display.addEventListener('wheel', (e) => {
        mouse.handleWheel(e);
      });
      
      // 调整显示大小
      this.resizeDisplay();
      window.addEventListener('resize', this.resizeDisplay);
    },
    
    resizeDisplay() {
      const display = document.getElementById('rdp-display');
      const width = display.clientWidth;
      const height = display.clientHeight;
      
      if (this.client) {
        this.client.getDisplay().resize(width, height);
        
        // 发送窗口大小调整消息
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({
            type: 1,
            data: {
              cols: width,
              rows: height
            }
          }));
        }
      }
    },
    
    disconnect() {
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      
      if (this.client) {
        this.client.disconnect();
        this.client = null;
      }
      
      if (this.connectionTimeout) {
        clearTimeout(this.connectionTimeout);
      }
      
      window.removeEventListener('resize', this.resizeDisplay);
    }
  }
};
</script>

<style scoped>
.rdp-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #f0f0f0;
}

.rdp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #333;
  color: white;
}

.disconnect-btn {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
}

.disconnect-btn:hover {
  background-color: #c82333;
}

.rdp-display {
  flex: 1;
  border: 1px solid #ddd;
  background-color: black;
  overflow: hidden;
}

.error-message {
  padding: 10px;
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  margin: 10px;
}
</style>
```

### 10.2 React组件示例

```jsx
import React, { useEffect, useRef, useState } from 'react';
import Guacamole from 'guacamole-common-js';

const RdpComponent = ({ resourceId, voucherId, token, resolution = '1024x768', colorDepth = 16, enableClipboard = true }) => {
  const displayRef = useRef(null);
  const [error, setError] = useState('');
  const wsRef = useRef(null);
  const clientRef = useRef(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, []);

  const connect = () => {
    const url = `ws://${window.location.host}/api/terminal/rdp/?token=${token}&resource_id=${resourceId}&voucher_id=${voucherId}&resolution=${resolution}&color_depth=${colorDepth}&enable_clipboard=${enableClipboard}`;

    wsRef.current = new WebSocket(url);

    // 设置连接超时
    timeoutRef.current = setTimeout(() => {
      setError('连接超时，请检查网络连接或服务器状态');
      disconnect();
    }, 10000);

    wsRef.current.addEventListener('open', () => {
      clearTimeout(timeoutRef.current);
      initGuacamole();
    });

    wsRef.current.addEventListener('error', (error) => {
      console.error('WebSocket错误:', error);
      setError('无法连接到远程服务器，请检查网络连接');
    });

    wsRef.current.addEventListener('close', (event) => {
      if (event.code !== 1000) {
        setError(`远程连接已关闭: ${event.reason}`);
      }
    });
  };

  const initGuacamole = () => {
    if (!displayRef.current) return;

    clientRef.current = new Guacamole.Client(wsRef.current);
    clientRef.current.getDisplay().attach(displayRef.current);

    // 处理键盘事件
    const keyboard = clientRef.current.getKeyboard();
    const handleKeyDown = (e) => keyboard.handleKeydown(e);
    const handleKeyUp = (e) => keyboard.handleKeyup(e);
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    // 处理鼠标事件
    const mouse = clientRef.current.getMouse();
    const display = displayRef.current;
    const handleMouseDown = (e) => mouse.handleMouseDown(e);
    const handleMouseMove = (e) => mouse.handleMouseMove(e);
    const handleMouseUp = (e) => mouse.handleMouseUp(e);
    const handleWheel = (e) => mouse.handleWheel(e);
    display.addEventListener('mousedown', handleMouseDown);
    display.addEventListener('mousemove', handleMouseMove);
    display.addEventListener('mouseup', handleMouseUp);
    display.addEventListener('wheel', handleWheel);

    // 调整显示大小
    resizeDisplay();
    const handleResize = resizeDisplay;
    window.addEventListener('resize', handleResize);

    // 清理函数
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
      display.removeEventListener('mousedown', handleMouseDown);
      display.removeEventListener('mousemove', handleMouseMove);
      display.removeEventListener('mouseup', handleMouseUp);
      display.removeEventListener('wheel', handleWheel);
      window.removeEventListener('resize', handleResize);
    };
  };

  const resizeDisplay = () => {
    if (!displayRef.current || !clientRef.current || !wsRef.current) return;

    const display = displayRef.current;
    const width = display.clientWidth;
    const height = display.clientHeight;

    clientRef.current.getDisplay().resize(width, height);

    // 发送窗口大小调整消息
    if (wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 1,
        data: {
          cols: width,
          rows: height
        }
      }));
    }
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
    }

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  };

  return (
    <div className="rdp-container">
      <div className="rdp-header">
        <h3>远程桌面连接</h3>
        <button onClick={disconnect} className="disconnect-btn">断开连接</button>
      </div>
      <div ref={displayRef} className="rdp-display"></div>
      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default RdpComponent;
```

## 11. 常见问题与解决方案

### 11.1 连接失败

**问题**: WebSocket连接失败，返回403错误
**解决方案**: 检查JWT令牌是否有效，确保用户有足够的权限访问该资源

### 11.2 画面卡顿

**问题**: RDP画面卡顿，响应缓慢
**解决方案**: 
- 降低分辨率和颜色深度
- 检查网络连接质量
- 确保Guacamole服务器性能足够

### 11.3 剪贴板功能不工作

**问题**: 无法在本地和远程桌面之间复制粘贴
**解决方案**: 确保enable_clipboard参数设置为true，检查Guacamole服务器配置

### 11.4 鼠标指针不同步

**问题**: 鼠标指针位置与实际点击位置不一致
**解决方案**: 确保正确处理鼠标事件，避免在事件处理中添加额外的偏移量

## 12. 总结

通过本文档的指导，前端开发人员可以成功对接RDP远程桌面功能，为用户提供流畅的远程Windows服务器访问体验。关键步骤包括：

1. 构建正确的WebSocket连接URL
2. 集成Guacamole客户端库
3. 处理键盘和鼠标事件
4. 实现错误处理和重连机制
5. 优化性能和用户体验

遵循这些步骤，可以开发出功能完整、性能良好的RDP前端应用。