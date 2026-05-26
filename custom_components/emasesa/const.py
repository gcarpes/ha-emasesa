"""Constantes para la integración EMASESA."""

DOMAIN = "emasesa"

# Config keys
CONF_CONTRATO = "contrato"

# API
API_BASE = "https://datosabiertos.emasesa.com/usuarios/api/v1.0"
API_TOKEN_URL = f"{API_BASE}/token"
API_CONSUMOS_URL = f"{API_BASE}/consumos/contrato"

# Update interval (seconds)
DEFAULT_SCAN_INTERVAL = 3600  # 1 hora

# Sensor names
SENSOR_CONSUMO_ULTIMO = "consumo_ultimo_periodo"
SENSOR_CONSUMO_TOTAL = "consumo_total"
SENSOR_CONSUMO_MEDIO = "consumo_medio"
SENSOR_LECTURA_CONTADOR = "lectura_contador"
