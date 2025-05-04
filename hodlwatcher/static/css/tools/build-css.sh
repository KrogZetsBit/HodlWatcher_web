#!/bin/bash

# Script para combinar y minificar los módulos CSS

# Directorio base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."

# Directorio de módulos
MODULES_DIR="$BASE_DIR/modules"

# Archivo de salida
OUTPUT_FILE="$BASE_DIR/main.min.css"

# Comprobar si tenemos csso instalado para minificación
if ! command -v csso &> /dev/null; then
    echo "CSSO no está instalado. Puedes instalarlo con 'npm install -g csso-cli'"
    echo "Continuando sin minificación..."
    HAS_CSSO=false
else
    HAS_CSSO=true
fi

# Crear un archivo temporal
TEMP_FILE=$(mktemp)

# Añadir declaración UTF-8
echo '@charset "UTF-8";' > "$TEMP_FILE"
echo '/* Archivo generado automáticamente - no editar directamente */' >> "$TEMP_FILE"
echo '/* Generado: '$(date)' */' >> "$TEMP_FILE"
echo '' >> "$TEMP_FILE"

# Módulos en orden de importancia
MODULES=(
    "variables.css"
    "base.css"
    "grid.css"
    "components.css"
    "utilities.css"
)

# Combinar archivos
for module in "${MODULES[@]}"; do
    if [ -f "$MODULES_DIR/$module" ]; then
        echo ">> Incluyendo $module"
        echo "/* $module */" >> "$TEMP_FILE"
        cat "$MODULES_DIR/$module" | grep -v '@charset' >> "$TEMP_FILE"
        echo "" >> "$TEMP_FILE"
    else
        echo "⚠️ Advertencia: El módulo $module no existe"
    fi
done

# Minificar si es posible
if [ "$HAS_CSSO" = true ]; then
    echo "Minificando CSS..."
    csso "$TEMP_FILE" --output "$OUTPUT_FILE"
else
    echo "Copiando CSS (sin minificar)..."
    cp "$TEMP_FILE" "$OUTPUT_FILE"
fi

# Mostrar tamaño
ORIGINAL_SIZE=$(wc -c < "$TEMP_FILE")
FINAL_SIZE=$(wc -c < "$OUTPUT_FILE")
SAVED=$((ORIGINAL_SIZE - FINAL_SIZE))
PERCENT=$((SAVED * 100 / ORIGINAL_SIZE))

echo ""
echo "🎉 Archivo CSS generado: $OUTPUT_FILE"
echo "Tamaño original: $ORIGINAL_SIZE bytes"
echo "Tamaño final: $FINAL_SIZE bytes"
echo "Ahorro: $SAVED bytes ($PERCENT%)"

# Limpiar
rm "$TEMP_FILE"

echo ""
echo "✅ Proceso completado"
