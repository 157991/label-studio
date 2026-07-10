@echo off
cd /d d:\extra\old\Lable-studio\label-studio
set DJANGO_DB=sqlite
set DJANGO_SETTINGS_MODULE=core.settings.label_studio
py -3.11 label_studio\manage.py runserver 0.0.0.0:8000
