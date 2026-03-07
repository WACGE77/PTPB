#!/usr/bin/env python3
"""检查权限配置"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BackEnd.settings')
django.setup()

from perm.models import ResourceGroupAuth
from resource.models import ResourceGroup
from rbac.models import Role

print("=== 权限配置检查 ===")

# 获取默认资源组和管理员角色
try:
    group = ResourceGroup.objects.get(name='Default')
    role = Role.objects.get(name='管理员')
    
    print(f"资源组: {group.name}")
    print(f"角色: {role.name}")
    
    # 检查权限
    auths = ResourceGroupAuth.objects.filter(resource_group=group, role=role)
    print(f"权限数量: {auths.count()}")
    
    for auth in auths:
        print(f"  - {auth.permission.code}")
        
    print("\n=== 检查完成 ===")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()