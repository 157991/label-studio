import os, sys
os.environ.setdefault("DJANGO_DB", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.label_studio")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'label_studio'))

import django
django.setup()
print("Django OK:", django.VERSION)

from django.conf import settings
print("STATIC_URL:", settings.STATIC_URL)
print("STATIC_ROOT:", settings.STATIC_ROOT)
print("STATICFILES_DIRS:", settings.STATICFILES_DIRS)
print("FRONTEND_HOSTNAME:", settings.FRONTEND_HOSTNAME)
print("FRONTEND_HMR:", settings.FRONTEND_HMR)
print("REACT_APP_ROOT:", getattr(settings, 'REACT_APP_ROOT', 'NOT FOUND'))

# 检查 manifest.json
import json
from pathlib import Path
manifest_path = Path(settings.STATIC_ROOT) / 'js' / 'manifest.json'
print("manifest exists:", manifest_path.exists())
if manifest_path.exists():
    with open(manifest_path) as f:
        m = json.load(f)
    print("manifest keys:", list(m.keys())[:20])
