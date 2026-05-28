# 💧 EMASESA Consumo de Agua — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/Gracarpes/ha-emasesa/releases)

Integración para **Home Assistant** que conecta con la API oficial de **EMASESA** (Empresa Metropolitana de Abastecimiento y Saneamiento de Aguas de Sevilla) para monitorizar el consumo de agua del contador inteligente.

---

## ✨ Características

- 📊 **Consumo horario** inyectado en las estadísticas de HA (panel de Energía)
- 📅 **Historial completo** desde el primer dato disponible en la API
- 🔄 **Actualización automática** configurable (por defecto cada hora)
- 🕐 **Zona horaria correcta** — horas en hora local de Madrid
- 🏠 **5 sensores** de consumo listos para automatizaciones
- ⚡ **Sin dependencias externas** — usa solo librerías incluidas en HA

## 🚀 Instalación

### Opción 1 — HACS (recomendado)

1. Abre HACS → Integraciones → ⋮ → Repositorios personalizados
2. Añade: `https://github.com/Gracarpes/ha-emasesa`
3. Categoría: **Integración**
4. Instala **EMASESA Consumo de Agua**
5. Reinicia Home Assistant

### Opción 2 — Manual

1. Descarga la carpeta `custom_components/emasesa/`
2. Cópiala en `/homeassistant/custom_components/emasesa/`
3. Reinicia Home Assistant

---

## ⚙️ Configuración

1. Ve a **Configuración → Dispositivos e integraciones → Añadir integración**
2. Busca **EMASESA**
3. Introduce tus credenciales:

| Campo | Descripción |
|-------|-------------|
| **DNI / Usuario** | Tu DNI o usuario de la web de EMASESA |
| **Contraseña** | Contraseña de tu cuenta en emasesa.com |
| **Número de contrato** | Aparece en tu factura (ej: `0202151225`) |
| **Intervalo de actualización** | Segundos entre consultas (mínimo recomendado: 3600) |

---

## 📡 Sensores creados

| Sensor | Descripción | Unidad |
|--------|-------------|--------|
| `sensor.emasesa_contrato_xxxxxxxxxx_emasesa_consumo_hoy` | Consumo del último día disponible | m³ |
| `sensor.emasesa_contrato_xxxxxxxxxx_emasesa_consumo_medio_diario` | Consumo medio diario | m³ |
| `sensor.emasesa_contrato_xxxxxxxxxx_emasesa_estado_contador` | OK INCIDENCIAS |
| `sensor.emasesa_contrato_xxxxxxxxxx_emasesa_error_contador` | True False posible error de lectura |
| `ssensor.emasesa_contrato_xxxxxxxxxx_emasesa_consumo_nocturno` | True False posibles fugas |

Además se crea la estadística externa `emasesa:agua_CONTRATO` con el consumo horario histórico, disponible en el **panel de Energía → Agua**.

---

## 📈 Panel de Energía

1. Ve a **Energía → Agua → Añadir consumo de agua**
2. Busca `emasesa:agua_TUCONTRATO`
3. Los datos históricos horarios aparecerán automáticamente

## 📊 Tarjeta Lovelace recomendada

```yaml
type: statistics-graph
title: Consumo de Agua EMASESA
entities:
  - entity: emasesa:agua_TUCONTRATO
    name: Consumo horario
stat_types:
  - state
chart_type: bar
period: hour
days_to_show: 7
```

---

## 🤝 Contribuir

Este proyecto lo mantengo en mi tiempo libre, sin ningún tipo de compromiso formal con EMASESA ni con ninguna otra organización. Lo comparto porque creo que puede ser útil para los ciudadanos de Sevilla que quieran monitorizar su consumo de agua.
Si encuentras algún bug, tienes una idea o quieres mejorar algo, los issues y pull requests son más que bienvenidos. Haré lo que pueda cuando pueda. 😊

---

## 📄 Licencia

MIT License — libre para usar, modificar y distribuir.
