import re
import json
from typing import List, Tuple, Optional

class SSHCommandBuffer:
    """SSH命令缓冲区，用于处理逐字符输入、编辑操作等"""
    
    def __init__(self):
        self.buffer = []  # 使用列表存储字符，便于编辑操作
        self.cursor = 0  # 光标位置
    
    def add_char(self, char: str):
        """添加字符到缓冲区"""
        self.buffer.insert(self.cursor, char)
        self.cursor += 1
    
    def backspace(self):
        """退格删除字符"""
        if self.cursor > 0:
            self.buffer.pop(self.cursor - 1)
            self.cursor -= 1
    
    def delete(self):
        """删除光标处字符"""
        if self.cursor < len(self.buffer):
            self.buffer.pop(self.cursor)
    
    def move_left(self):
        """光标左移"""
        if self.cursor > 0:
            self.cursor -= 1
    
    def move_right(self):
        """光标右移"""
        if self.cursor < len(self.buffer):
            self.cursor += 1
    
    def move_to_start(self):
        """光标移到开始"""
        self.cursor = 0
    
    def move_to_end(self):
        """光标移到结束"""
        self.cursor = len(self.buffer)
    
    def clear(self):
        """清空缓冲区"""
        self.buffer = []
        self.cursor = 0
    
    def get_content(self) -> str:
        """获取缓冲区内容"""
        return ''.join(self.buffer)
    
    def set_content(self, content: str):
        """设置缓冲区内容"""
        self.buffer = list(content)
        self.cursor = len(self.buffer)
    
    def is_empty(self) -> bool:
        """检查缓冲区是否为空"""
        return len(self.buffer) == 0
    
    def get_command(self) -> str:
        """获取完整命令"""
        return ''.join(self.buffer)
    
    def process_input(self, data: str) -> List[str]:
        """处理输入数据，返回需要发送到前端的字符"""
        output = []
        i = 0
        while i < len(data):
            char = data[i]
            # 检查是否是转义序列（ESC开头）
            if char == '\x1b' and i + 2 < len(data):
                # 检查是否是光标移动序列
                if data[i+1] == '[':
                    seq = data[i:i+3]
                    # 所有方向键都直接发送到服务器
                    output.append(seq)
                    i += 3
                    continue
            
            if char == '\x08' or char == '\x7f':  # Backspace or Delete
                if self.cursor > 0:
                    self.backspace()
                    output.append('\x08\x20\x08')  # 退格、空格、退格，用于清除屏幕上的字符
            elif char == '\x03':  # Ctrl+C
                self.clear()
                output.append('\r\n')
            elif char == '\r' or char == '\n':  # 回车
                self.add_char('\n')
                output.append('\r\n')
            else:
                self.add_char(char)
                output.append(char)
            i += 1
        return output

class SSHBlacklistMatcher:
    """SSH黑名单匹配器，用于匹配命令是否在黑名单中"""
    
    def __init__(self):
        self.rules = []  # 规则列表
    
    def add_rule(self, pattern: str, rule_type: str = 'exact'):
        """添加规则"""
        self.rules.append((pattern, rule_type))
    
    def match(self, command: str) -> Tuple[bool, Optional[str]]:
        """匹配命令是否在黑名单中"""
        command = command.strip()
        if not command:
            return False, None
        
        for pattern, rule_type in self.rules:
            pattern = pattern.strip()
            if not pattern:
                continue
            
            # 精确匹配
            if rule_type == 'exact':
                if command == pattern:
                    return True, f'匹配精确规则: {pattern}'
            # 前缀匹配
            elif rule_type == 'prefix':
                if command.startswith(pattern):
                    return True, f'匹配前缀规则: {pattern}'
            # 正则匹配
            elif rule_type == 'regex':
                try:
                    if re.search(pattern, command):
                        return True, f'匹配正则规则: {pattern}'
                except re.error:
                    pass
        
        return False, None
    
    def match_commands(self, commands: List[str]) -> List[Tuple[str, bool, Optional[str]]]:
        """匹配多条命令"""
        results = []
        for command in commands:
            matched, reason = self.match(command)
            results.append((command, matched, reason))
        return results
