import re
import logging
from .models import DangerCommandRule
from .cache import get_cached_rules, set_cached_rules

logger = logging.getLogger(__name__)

class CommandFilter:
    def __init__(self, group_id):
        self.group_id = group_id
    
    async def check_command(self, command):
        rules = await self._get_filter_rules()
        
        logger.info(f"检查命令: {command}")
        logger.info(f"规则数量: {len(rules)}")
        
        rules.sort(key=lambda x: x.priority, reverse=True)
        
        for rule in rules:
            try:
                pattern = rule.pattern.strip()
                if not pattern:
                    continue
                
                command_stripped = command.strip()
                
                if rule.type == 'exact':
                    if command_stripped == pattern:
                        return False, f'命中危险命令规则(精确): {rule.pattern}'
                elif rule.type == 'prefix':
                    actual_pattern = pattern[:-1] if pattern.endswith('*') else pattern
                    if command_stripped.startswith(actual_pattern):
                        return False, f'命中危险命令规则(前缀): {rule.pattern}'
                elif rule.type == 'regex':
                    try:
                        if re.search(pattern, command_stripped):
                            return False, f'命中危险命令规则(正则): {rule.pattern}'
                    except re.error as e:
                        logger.error(f"正则错误: {e}")
            except Exception as e:
                logger.error(f"错误: {e}")
        return True, ''
    
    async def _get_filter_rules(self):
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def get_rules():
            return list(DangerCommandRule.objects.filter(group_id=self.group_id, is_active=True))
        
        return await get_rules()
    
    async def check_commands(self, commands):
        results = []
        for command in commands:
            command = command.strip()
            if command:
                allowed, reason = await self.check_command(command)
                results.append((command, allowed, reason))
        return results
