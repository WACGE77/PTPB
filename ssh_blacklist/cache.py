import json
from django.core.cache import cache

# 缓存键前缀
CACHE_PREFIX = 'ssh_blacklist'

# 缓存过期时间（秒）
CACHE_EXPIRE_TIME = 3600

def get_cache_key(group_id, key):
    """获取缓存键"""
    return f'{CACHE_PREFIX}:{group_id}:{key}'

def get_cached_rules(group_id):
    """获取缓存的规则"""
    key = get_cache_key(group_id, 'rules')
    rules = cache.get(key)
    return rules

def set_cached_rules(group_id, rules):
    """设置缓存的规则"""
    key = get_cache_key(group_id, 'rules')
    cache.set(key, rules, CACHE_EXPIRE_TIME)

def get_cached_mode(group_id):
    """获取缓存的模式"""
    key = get_cache_key(group_id, 'mode')
    mode = cache.get(key)
    return mode

def set_cached_mode(group_id, mode):
    """设置缓存的模式"""
    key = get_cache_key(group_id, 'mode')
    cache.set(key, mode, CACHE_EXPIRE_TIME)

def clear_cache(group_id):
    """清除缓存"""
    key_pattern = f'{CACHE_PREFIX}:{group_id}:*'
    # 由于 Django 缓存 API 不支持模式删除，这里我们直接删除规则和模式的缓存
    rules_key = get_cache_key(group_id, 'rules')
    mode_key = get_cache_key(group_id, 'mode')
    cache.delete(rules_key)
    cache.delete(mode_key)
