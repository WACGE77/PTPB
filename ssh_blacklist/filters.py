import re
import logging
from .models import SSHCommandFilter
from .cache import get_cached_rules, set_cached_rules

logger = logging.getLogger(__name__)

class CommandFilter:
    def __init__(self, group_id):
        self.group_id = group_id
    
    async def check_command(self, command):
        # 获取系统组的命令过滤规则
        rules = await self._get_filter_rules()
        
        # 打印调试信息
        logger.info(f"检查命令: {command}")
        logger.info(f"规则数量: {len(rules)}")
        for rule in rules:
            logger.info(f"规则: {rule.pattern}, 类型: {rule.type}, 优先级: {rule.priority}")
        
        # 按优先级排序规则
        rules.sort(key=lambda x: x.priority, reverse=True)
        
        # 黑名单模式：默认允许，只阻止匹配规则的命令
        for rule in rules:
            try:
                # 检查命令是否匹配规则
                pattern = rule.pattern.strip()
                if not pattern:
                    continue
                
                # 处理规则模式
                command_stripped = command.strip()
                
                # 打印匹配信息
                logger.info(f"匹配检查: 命令='{command_stripped}', 模式='{pattern}', 类型='{rule.type}'")
                
                # 精确匹配
                if rule.type == 'exact':
                    if command_stripped == pattern:
                        logger.info(f"精确匹配成功: {command_stripped} == {pattern}")
                        return False, f'匹配黑名单规则: {rule.pattern}'
                # 前缀匹配
                elif rule.type == 'prefix':
                    if command_stripped.startswith(pattern):
                        logger.info(f"前缀匹配成功: {command_stripped} 以 {pattern} 开头")
                        return False, f'匹配黑名单规则: {rule.pattern}'
                # 正则匹配
                elif rule.type == 'regex':
                    try:
                        if re.search(pattern, command_stripped):
                            logger.info(f"正则匹配成功: {command_stripped} 匹配 {pattern}")
                            return False, f'匹配黑名单规则: {rule.pattern}'
                    except re.error as e:
                        logger.error(f"正则错误: {e}")
            except Exception as e:
                logger.error(f"错误: {e}")
        logger.info(f"命令 {command} 未匹配任何规则")
        return True, ''
    
    async def _get_filter_rules(self):
        # 直接从数据库获取（暂时不使用缓存，避免序列化问题）
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def get_rules():
            logger.info(f"从数据库获取规则，组ID: {self.group_id}")
            rules = list(SSHCommandFilter.objects.filter(group_id=self.group_id))
            logger.info(f"获取到 {len(rules)} 条规则")
            return rules
        
        rules = await get_rules()
        return rules
    
    async def check_commands(self, commands):
        """检查多条命令"""
        results = []
        for command in commands:
            command = command.strip()
            if command:
                allowed, reason = await self.check_command(command)
                results.append((command, allowed, reason))
        return results
