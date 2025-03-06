@echo off
chcp 65001
cd /d %~dp0
xiexievpn.exe %1
exit /B