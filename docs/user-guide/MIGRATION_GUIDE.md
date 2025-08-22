# Migration Guide: 0.1.0 → 0.2.0

## 🔐 **Fullständig bakåtkompatibilitet garanterad**

**Alla funktioner från version 0.1.0 fungerar exakt likadant i version 0.2.0.** Du behöver inte ändra någon kod eller kommandon för att uppgradera.

## ✅ **Vad som fungerar identiskt**

### **CLI-kommandot**
```bash
# Detta fungerar exakt som i 0.1.0:
reporthanter \
  --blastn_file results.csv \
  --kraken_file kraken.tsv \
  --kaiju_table kaiju.tsv \
  --fastp_json fastp.json \
  --flagstat_file flagstat.txt \
  --coverage_folder plots/ \
  --output report.html \
  --sample_name "Sample1"
```

### **Python API**
```python
# Alla legacy-funktioner fungerar som förut:
from reporthanter import (
    panel_report,           # Huvudfunktionen
    plot_kraken,            # Kraken-diagram
    plot_kaiju,             # Kaiju-diagram
    plot_blastn,            # BLAST-diagram
    parse_fastp_json,       # FastP-parsing
    alignment_stats,        # Alignment-statistik
    # ... alla andra funktioner
)

# Samma användning som i 0.1.0:
report = panel_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv", 
    kaiju_table="kaiju.tsv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    coverage_folder="plots/",
    sample_name="Test"
)
```

## 🚀 **Nya förbättringar (valfria)**

### **1. Förbättrat CLI med validering**
```bash
# Nya alternativ (bakåtkompatibla):
reporthanter \
  --config_file my_config.json \  # Anpassad konfiguration
  --validate_only \                # Bara validera filer
  --log_level DEBUG \              # Mer detaljerad loggning
  # ... alla gamla argument fungerar också
```

### **2. Ny robust API**
```python
# Ny rekommenderad approach (mer robust):
from reporthanter import ReportGenerator, DefaultConfig

# Med konfiguration
config = DefaultConfig('my_config.json')
generator = ReportGenerator(config)

report = generator.generate_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv", 
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    coverage_folder="plots/",
    sample_name="Test"
)

generator.save_report(report, "output.html")
```

### **3. Enskilda processors (för avancerade användare)**
```python
# Bearbeta enskilda datatyper:
from reporthanter import KrakenProcessor, KrakenPlotGenerator

processor = KrakenProcessor()
data = processor.process("kraken_file.tsv")
filtered_data, unclassified = processor.filter_data(data)

plot_gen = KrakenPlotGenerator()
chart = plot_gen.generate_plot(filtered_data)
```

## 📋 **Vad är nytt i 0.2.0**

### **Förbättrad arkitektur**
- ✅ Robustare felhantering
- ✅ Bättre validering av input-filer
- ✅ Konfigurerbar styling och beteende
- ✅ Modulär design för enklare underhåll
- ✅ Fullständiga type hints

### **Utvecklarverktyg**
- ✅ Testsuite med pytest
- ✅ Code formatting med Black
- ✅ Linting med flake8 och mypy
- ✅ Pre-commit hooks
- ✅ Makefile för utvecklingsworkflow

### **Bättre felhantering**
```python
# Fångar nu specifika fel istället för allmänna:
from reporthanter import ReportHanterError, DataProcessingError

try:
    report = panel_report(...)
except DataProcessingError as e:
    print(f"Problem med dataprocessing: {e}")
except ReportHanterError as e:
    print(f"Allmänt ReportHanter-fel: {e}")
```

## 📝 **Konfiguration**

### **Skapa config-fil (valfritt)**
```json
{
  "plotting": {
    "width": "container",
    "height": 500,
    "color_scheme": "category20"
  },
  "filtering": {
    "kraken": {
      "level": "species",
      "cutoff": 0.005,
      "max_entries": 15,
      "virus_only": true
    }
  },
  "report": {
    "header_color": "#2E8B57"
  }
}
```

## 🔄 **Migrationsplan**

### **Fas 1: Ingen ändring krävs (NU)**
- ✅ Uppgradera till 0.2.0 utan kodändringar
- ✅ Allt fungerar som förut
- ✅ Få tillgång till bättre felmeddelanden och logging

### **Fas 2: Gradvis migration (vid behov)**
- 🔄 Börja använda `ReportGenerator` för nya projekt
- 🔄 Lägg till konfigurationsfiler för anpassning
- 🔄 Använd nya CLI-alternativ för bättre validering

### **Fas 3: Framtida (eventuellt)**
- ⚠️ Legacy-funktioner kommer att märkas som "deprecated" i framtida versioner
- ⚠️ De kommer fortfarande att fungera, men med varningar
- ✅ Migration kommer att vara frivillig och väl dokumenterad

## 🧪 **Testa din migration**

Kör vårt kompatibilitetstest:
```bash
python3 compatibility_check.py
```

## 🆘 **Support**

Om du stöter på problem efter uppgradering:

1. **Kontrollera att alla dependencies är installerade:**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Validera dina input-filer:**
   ```bash
   reporthanter --validate_only --log_level DEBUG [dina arguments]
   ```

3. **Använd legacy API om något inte fungerar:**
   ```python
   # Fallback till 0.1.0 API:
   from reporthanter import panel_report  # Gammal, pålitlig funktion
   ```

4. **Rapportera buggar:** Skapa en issue på GitHub med detaljerad information

---

**Sammanfattning:** Version 0.2.0 är en drop-in replacement för 0.1.0 med massvis av förbättringar under huven, men ingen brytande förändring av API:et.