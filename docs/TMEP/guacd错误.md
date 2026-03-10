# GuacamoleClient 实现问题整理

## 一、connect 参数格式错误（最严重）

当前代码：

```python
connection_string = json.dumps(connection_params)
param_message = f"{len(connection_string)}.{connection_string};"
```

问题：

guacd **不支持 JSON 参数**。
Guacamole 协议必须使用：

```
length.value,length.value,length.value;
```

例如 SSH 连接正确格式：

```
7.connect,9.127.0.0.1,2.22,4.root,8.password;
```

而当前代码实际发送的是：

```
6.select,3.ssh;52.{"protocol":"ssh","hostname":"..."}
```

这会导致：

* guacd 解析失败
* 服务器立即断开连接
* 出现 `WinError 10053`

解决方案：

必须改为逐个参数编码：

```
len(arg).arg
```

---

## 二、缺少 size 指令

Guacamole 连接流程必须按顺序：

```
select
↓
args (服务器返回)
↓
size
↓
connect
↓
sync
```

当前代码流程：

```
select
↓
connect
```

缺少：

```
size
```

正确示例：

```
6.select,3.ssh;
4.size,3.120,2.40;
7.connect,...
```

---

## 三、未处理 args 返回

在 `select` 之后，guacd 会返回：

```
4.args,4.host,4.port,8.username,8.password;
```

含义：

```
connect 指令需要的参数顺序
```

当前代码：

```
select → 直接 connect
```

问题：

如果参数顺序不匹配，guacd 会：

```
disconnect
```

正确流程：

```
select
↓
读取 args
↓
根据 args 构建 connect
```

---

## 四、send() 实现不符合协议

当前实现：

```python
guac_message = f"{len(data)}.{data}"
```

问题：

Guacamole 指令必须是：

```
instruction,arg1,arg2;
```

例如：

```
5.stdin,2.ls;
```

而当前代码会发送：

```
2.ls
```

这是 **非法协议消息**。

---

## 五、resize() 使用 JSON（错误）

当前代码：

```python
resize_command = json.dumps({
    "type": "size",
    "width": cols,
    "height": rows
})
```

问题：

Guacamole **不使用 JSON**。

正确格式：

```
4.size,3.120,2.40;
```

---

## 六、_recv_loop() 解析不完整

当前解析方式：

```
按 ; 分割
```

但 Guacamole 指令内部结构是：

```
length.string
```

例如：

```
6.stdout,12.hello world!;
```

需要进一步解析：

```
stdout
hello world!
```

否则无法正确处理：

* stdout
* stderr
* clipboard
* file transfer

---

## 七、resize() 中存在未定义变量

代码：

```python
if self._websocket and not self._websocket.closed:
```

问题：

类中 **没有定义 `_websocket`**。

运行时会触发：

```
AttributeError
```

---

## 八、缺少 stdin 指令实现

SSH 交互必须使用：

```
5.stdin,2.ls;
```

当前 `send()` 没有实现：

```
stdin
```

因此无法真正执行远程命令。

---

## 九、未实现 sync 机制

连接成功后 guacd 会返回：

```
4.sync,12345;
```

客户端必须回应：

```
4.sync,12345;
```

否则会出现：

```
会话卡住
```

当前代码没有处理。

---

# 总结

当前代码结构：

| 模块             | 状态       |
| -------------- | -------- |
| async 架构       | ✅ 正常     |
| 类设计            | ✅ 清晰     |
| 配置加载           | ✅ 正常     |
| Guacamole 协议实现 | ❌ 存在多处错误 |

核心问题：

**把 guacd 当成 JSON API 使用了。**

而实际上它是：

```
length.string,length.string;
```

---

# 推荐改进方向

实现一个统一编码函数：

```python
def guac(*args):
    parts = []
    for a in args:
        a = str(a)
        parts.append(f"{len(a)}.{a}")
    return ",".join(parts) + ";"
```

使用方式：

```
guac("select","ssh")
guac("size",120,40)
guac("connect",host,port,user,password)
```

---

# 正确通信流程示例

客户端：

```
6.select,3.ssh;
```

服务器：

```
4.args,4.host,4.port,8.username,8.password;
```

客户端：

```
4.size,3.120,2.40;
7.connect,9.127.0.0.1,2.22,4.root,8.password;
```

服务器：

```
4.sync,12345;
```

客户端：

```
4.sync,12345;
```

然后进入：

```
stdin / stdout
```

---

# 结论

当前代码问题主要集中在 **Guacamole 协议实现错误**，需要：

1. 移除 JSON 参数
2. 按协议编码消息
3. 实现 args 解析
4. 补充 size / sync
5. 正确实现 stdin / stdout
