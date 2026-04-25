import json
from django.core.cache import cache

CACHE_PREFIX = 'danger_cmd'
CACHE_EXPIRE_TIME = 3600

def get_cache_key(group_id, key):
    return f'{CACHE_PREFIX}:{group_id}:{key}'

def get_cached_rules(group_id):
    key = get_cache_key(group_id, 'rules')
    rules = cache.get(key)
    return rules

def set_cached_rules(group_id, rules):
    key = get_cache_key(group_id, 'rules')
    cache.set(key, rules, CACHE_EXPIRE_TIME)

def get_cached_mode(group_id):
    key = get_cache_key(group_id, 'mode')
    mode = cache.get(key)
    return mode

def set_cached_mode(group_id, mode):
    key = get_cache_key(group_id, 'mode')
    cache.set(key, mode, CACHE_EXPIRE_TIME)

def clear_cache(group_id):
    key_pattern = f'{CACHE_PREFIX}:{group_id}:*'
    rules_key = get_cache_key(group_id, 'rules')
    mode_key = get_cache_key(group_id, 'mode')
    cache.delete(rules_key)
    cache.delete(mode_key)
