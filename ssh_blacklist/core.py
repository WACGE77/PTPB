import json
from typing import List, Tuple, Optional

class SSHCommandBuffer:
    """SSH命令缓冲区，用于处理逐字符输入、编辑操作等"""
    
    def __init__(self):
        self.buffer = []
        self.cursor = 0
    
    def add_char(self, char: str):
        self.buffer.insert(self.cursor, char)
        self.cursor += 1
    
    def backspace(self):
        if self.cursor > 0:
            self.buffer.pop(self.cursor - 1)
            self.cursor -= 1
    
    def delete(self):
        if self.cursor < len(self.buffer):
            self.buffer.pop(self.cursor)
    
    def move_left(self):
        if self.cursor > 0:
            self.cursor -= 1
    
    def move_right(self):
        if self.cursor < len(self.buffer):
            self.cursor += 1
    
    def move_to_start(self):
        self.cursor = 0
    
    def move_to_end(self):
        self.cursor = len(self.buffer)
    
    def clear(self):
        self.buffer = []
        self.cursor = 0
    
    def get_content(self) -> str:
        return ''.join(self.buffer)
    
    def set_content(self, content: str):
        self.buffer = list(content)
        self.cursor = len(content)
    
    def is_empty(self) -> bool:
        return len(self.buffer) == 0
    
    def get_command(self) -> str:
        return ''.join(self.buffer)
    
    def process_input(self, data: str) -> List[str]:
        output = []
        i = 0
        while i < len(data):
            char = data[i
]
            if char == '\x1b' and i + 2 < len(data):
                if data[i+1] == '[':
                    seq = data[i:i+3]
                    output.append(seq)
                    i += 3
                    continue
            
            if char == '\x08' or char == '\x7f':
                if self.cursor > 0:
                    self.backspace()
                    output.append('\x08\x20\x08')
            elif char == '\x03':
                self.clear()
                output.append('\r\n')
            elif char == '\r' or char == '\n':
                self.add_char('\n')
                output.append('\r\n')
            else:
                self.add_char(char)
                output.append(char)
            i += 1
        return output


class DangerCommandMatcher:
    """危险命令匹配器，用于检测命令是否命中告警规则"""
    
    def __init__(self):
        self.rules = []
    
    def add_rule(self, pattern: str, rule_type: str = 'exact'):
        self.rules.append((pattern, rule_type))
    
    def match(self, command: str) -> Tuple[bool, Optional[str]]:
        command = command.strip()
        if not command:
            return False, None
        
        for pattern, rule_type in self.rules:
            pattern = pattern.strip()
            if not pattern:
                continue
            
            if rule_type == 'exact':
                if command == pattern:
                    return True, f'命中精确规则: {pattern}'
            elif rule_type == 'prefix':
                if command.startswith(pattern):
                    return True, f'命中前缀规则: {pattern}'
            elif rule_type == 'regex':
                try:
                    if re.search(pattern, command):
                        return True, f'命中正则规则: {pattern}'
                except re.error:
                    pass
        
        return False, None
    
    def match_commands(self, commands: List[str]) -> List[Tuple[str, bool, Optional[str]]]:
        results = []
        for command in commands:
            matched, reason = self.match(command)
            results.append((command, matched, reason))
        return results
