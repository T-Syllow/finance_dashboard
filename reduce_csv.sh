#!/bin/bash

# Name der Originaldatei
INPUT_FILE="newData/cleaned_transaction_data_mio.csv"

# Name der Zieldatei
OUTPUT_FILE="newData/cleaned_transaction_data_500k.csv"

# Anzahl der gewünschten Zeilen (inkl. Header)
LINES_TO_KEEP=500001  # 500.000 Datenzeilen + 1 Headerzeile

# Prüfen, ob die Datei existiert
if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Datei '$INPUT_FILE' nicht gefunden."
  exit 1
fi

# Datei kürzen
head -n $LINES_TO_KEEP "$INPUT_FILE" > "$OUTPUT_FILE"

echo "Datei '$OUTPUT_FILE' mit den ersten $((LINES_TO_KEEP - 1)) Datensätzen wurde erstellt."

