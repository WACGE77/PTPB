#!/usr/bin/env python3
"""检查用户和角色配置"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BackEnd.settings')
django.setup()

from rbac.models import User, Role

print("=== 用户和角色配置检查 ===")

# 检查所有角色
print("\n1. 所有角色:")
roles = Role.objects.all()
for role in roles:
    print(f"  - {role.name}")

# 检查所有用户
print("\n2. 所有用户:")
users = User.objects.all()
for user in users:
    print(f"  - {user.account}")
    user_roles = user.roles.all()
    print(f"    角色: {[r.name for r in user_roles]}")

print("\n=== 检查完成 ===")