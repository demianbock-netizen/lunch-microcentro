#!/bin/bash
# Doble click para abrir Lunch Microcentro en Mac
cd "$(dirname "$0")"

# Determinar comando de Python disponible
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "❌ Python 3 no está instalado."
    echo "Instalalo desde https://www.python.org/downloads/"
    read -p "Presioná Enter para cerrar..."
    exit 1
fi

# Verificar que streamlit esté instalado (no solo que exista la carpeta venv)
if [ ! -x "venv/bin/streamlit" ]; then
    echo "📦 Instalando dependencias (1-2 minutos, mostrando progreso)..."

    # Borrar venv roto si existe
    rm -rf venv

    # Crear venv nuevo
    $PYTHON -m venv venv
    if [ ! -f "venv/bin/pip" ]; then
        echo ""
        echo "❌ No se pudo crear el entorno virtual."
        echo "Verificá tu instalación de Python."
        read -p "Presioná Enter para cerrar..."
        exit 1
    fi

    # Instalar dependencias (con output visible)
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt

    # Verificar que streamlit se haya instalado
    if [ ! -x "venv/bin/streamlit" ]; then
        echo ""
        echo "❌ La instalación falló. Probá conectarte a internet y reintentar."
        read -p "Presioná Enter para cerrar..."
        exit 1
    fi
    echo ""
    echo "✓ Instalación lista."
fi

echo ""
echo "🍽️  Abriendo Lunch Microcentro en el navegador..."
echo "    Para cerrar: cerrá esta ventana."
echo ""
./venv/bin/streamlit run app.py
