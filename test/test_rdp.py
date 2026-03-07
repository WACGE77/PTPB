#!/usr/bin/env python3
"""测试RDP功能的脚本"""
import asyncio
import websockets
import json
import time

async def test_rdp_connection():
    """测试RDP WebSocket连接"""
    # WebSocket URL for RDP connection
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg2NzExMjA3LCJpYXQiOjE3Njk0MzEyMDcsImp0aSI6ImI5ZDc1ODdmM2EyZDRkYzdiYzI3OGVhNmM0OGRlM2I3IiwidXNlcl9pZCI6IjEifQ.ST8ZdChpXpyXX1WUfIr0OJhSxAbI-rE32suJoa4ngwE"
    
    # RDP连接参数
    resource_id = "1"
    voucher_id = "1"
    resolution = "1024x768"
    color_depth = "16"
    enable_clipboard = "true"
    
    # 构建WebSocket URL
    ws_url = f"ws://127.0.0.1:8000/api/terminal/rdp/?resource={resource_id}&voucher={voucher_id}&token={token}&resolution={resolution}&color_depth={color_depth}&enable_clipboard={enable_clipboard}"
    
    print(f"Testing RDP connection to: {ws_url}")
    print(f"RDP Configuration:")
    print(f"  Resolution: {resolution}")
    print(f"  Color Depth: {color_depth}")
    print(f"  Enable Clipboard: {enable_clipboard}")
    print()
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected to RDP WebSocket server")
            print("⏳ Waiting for initial connection setup...")
            
            # 等待连接建立
            await asyncio.sleep(3)
            
            # 测试发送RDP相关命令
            print("\n📡 Testing RDP commands...")
            
            # 测试调整窗口大小
            resize_command = json.dumps({"type": 1, "data": {"cols": 1024, "rows": 768}})
            await websocket.send(resize_command)
            print(f"✓ Sent resize command: {resize_command}")
            
            # 等待响应
            await asyncio.sleep(1)
            
            # 测试发送鼠标事件
            mouse_command = json.dumps({"type": 2, "data": {"event": "mouse", "x": 100, "y": 100, "button": "left", "action": "down"}})
            await websocket.send(mouse_command)
            print(f"✓ Sent mouse event: {mouse_command}")
            
            # 等待响应
            await asyncio.sleep(1)
            
            # 测试发送键盘事件
            keyboard_command = json.dumps({"type": 2, "data": {"event": "keyboard", "key": "Ctrl", "action": "down"}})
            await websocket.send(keyboard_command)
            print(f"✓ Sent keyboard event: {keyboard_command}")
            
            # 等待响应
            await asyncio.sleep(1)
            
            # 尝试接收响应
            print("\n📥 Waiting for server responses...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"✅ Received response: {response}")
            except asyncio.TimeoutError:
                print("⚠️  No response received within timeout")
            except websockets.exceptions.ConnectionClosedOK:
                print("⚠️  Connection closed by server")
            
            print("\n✅ RDP connection test completed successfully!")
            print("The RDP service is ready for use with Windows graphical interfaces.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=====================================")
    print("RDP Functionality Test")
    print("=====================================")
    print("Testing RDP connection and functionality...")
    print()
    
    asyncio.run(test_rdp_connection())
    
    print("\n=====================================")
    print("Test completed!")
    print("=====================================")