#!/bin/bash

# Name der Originaldatei
INPUT_FILE="./transactions_data.csv"

# Name der Zieldatei
OUTPUT_FILE="./transactions_data_mio.csv"

# Anzahl der gewünschten Zeilen (inkl. Header)
LINES_TO_KEEP=1000001  # 1.000.000 Datenzeilen + 1 Headerzeile

# Prüfen, ob die Datei existiert
if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Datei '$INPUT_FILE' nicht gefunden."
  exit 1
fi

# Datei zufällig mischen und kürzen
{ head -n 1 "$INPUT_FILE"; tail -n +2 "$INPUT_FILE" | shuf | head -n $((LINES_TO_KEEP - 1)); } > "$OUTPUT_FILE"

echo "Datei '$OUTPUT_FILE' mit den ersten $((LINES_TO_KEEP - 1)) zufällig ausgewählten Datensätzen wurde erstellt."