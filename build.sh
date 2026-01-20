#!/bin/bash

# Script master para buildear todo
# Uso: bash build.sh [mac|windows|all]

OPTION="${1:-all}"

echo "================================================"
echo "Banco de Alimentos - Build Script"
echo "================================================"
echo ""

case $OPTION in
    mac)
        echo "🍎 Compilando para macOS..."
        bash build_mac.sh
        ;;
    windows)
        echo "🪟 Compilando para Windows..."
        bash build_windows.sh
        ;;
    all)
        echo "📦 Compilando para ambas plataformas..."
        echo ""
        echo "🍎 Iniciando build macOS..."
        bash build_mac.sh
        echo ""
        echo "🪟 Mostrando instrucciones Windows..."
        bash build_windows.sh
        ;;
    *)
        echo "Uso: bash build.sh [mac|windows|all]"
        echo ""
        echo "Ejemplos:"
        echo "  bash build.sh mac      - Compilar solo para macOS"
        echo "  bash build.sh windows  - Mostrar instrucciones Windows"
        echo "  bash build.sh all      - Compilar para ambas plataformas"
        exit 1
        ;;
esac

echo ""
echo "Hecho! ✅"
