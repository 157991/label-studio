import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.label_studio')
os.environ.setdefault('DJANGO_DB', 'sqlite')
os.environ.setdefault('LABEL_STUDIO_DISABLE_SENTRY', 'true')
os.environ.setdefault('CHECK_FOR_UPDATES', 'false')

import django
django.setup()

from users.models import User

# 重置密码
for email in ['1579912185@qq.com', 'admin@admin.com', 'test@test.com']:
    try:
        u = User.objects.get(email=email)
        u.set_password('test123456')
        u.save()
        print(f'已重置: {email}')
    except User.DoesNotExist:
        print(f'不存在: {email}')

print('完成')
