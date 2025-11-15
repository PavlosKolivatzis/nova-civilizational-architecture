@echo off
set PY=C:\Python313\python.exe
cd /d C:\code\nova-civilizational-architecture
%PY% scripts\slot10_weekly_chaos.py --seed 42 --export-dir artifacts --export-prom slot10_metrics.prom
