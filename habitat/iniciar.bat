@echo off
rem Abre el Habitat de Madreperla conectado a Hermes (Windows: doble clic).
cd /d "%~dp0"
where py >nul 2>nul && (py puente\servidor.py) || (python puente\servidor.py)
pause
