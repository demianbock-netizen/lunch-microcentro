@echo off
REM Doble click para abrir Lunch Microcentro en Windows
cd /d "%~dp0"

REM Verificar Python
where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo [X] Python 3 no esta instalado.
    echo Instalalo desde https://www.python.org/downloads/
    echo IMPORTANTE: marca la opcion "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

REM Verificar que streamlit este instalado (no solo que exista venv)
if not exist "venv\Scripts\streamlit.exe" (
    echo.
    echo [*] Instalando dependencias (1-2 minutos)...

    REM Borrar venv roto si existe
    if exist "venv\" rmdir /s /q venv

    REM Crear venv nuevo
    python -m venv venv
    if not exist "venv\Scripts\pip.exe" (
        echo.
        echo [X] No se pudo crear el entorno virtual.
        echo Verifica tu instalacion de Python.
        pause
        exit /b 1
    )

    REM Instalar dependencias con output visible
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\pip.exe install -r requirements.txt

    REM Verificar que streamlit se haya instalado
    if not exist "venv\Scripts\streamlit.exe" (
        echo.
        echo [X] La instalacion fallo. Conectate a internet y reintenta.
        pause
        exit /b 1
    )
    echo.
    echo [v] Instalacion lista.
)

echo.
echo [+] Abriendo Lunch Microcentro en el navegador...
echo     Para cerrar: cerra esta ventana.
echo.
venv\Scripts\streamlit.exe run app.py
