# AtmosGear — Documentación Abierta e Ingeniería Inversa

> **[English](README.md) | [Español](README.es.md)**

Documentación técnica comunitaria, copias de seguridad reales de fábrica (**VESC v5.02**), análisis del protocolo UART del mando **Remote AG1 (Flipsky VX1)**, esquemas de conexión y herramientas en Python para los patines eléctricos **AtmosGear**.

Como apenas existe documentación técnica pública sobre la electrónica interna de los AtmosGear, su configuración VESC ni los menús ocultos del mando, este repositorio recopila todos los hallazgos verificados directamente sobre hardware real para ayudar a otros usuarios, reparadores y entusiastas.

---

## Resumen de Hallazgos Clave

- **Arquitectura Dual VESC:** Dentro de la riñonera hay **dos controladoras STM32F405** con **VESC Firmware v5.02 (`HW: 410`)**, enlazadas por un **bus CAN interno a 500 kbps**:
  - **ESC Maestro:** CAN ID `64`
  - **ESC Esclavo:** CAN ID `66` (`m_invert_direction = 1` por ir los motores enfrentados)
- **Configuración VESC v5.02 estándar:** Firmas oficiales (`MCCONF = 0x83d6207a`, `APPCONF = 0xc29ad144`), modo **FOC Sensorless**, **`±22.0 A`** por patín, rampa de aceleración `0.80 s`, rampa de frenada `0.40 s`, zona muerta `15%`, control por **`APP_UART`** a `115200` baudios.
- **Remote AG1 = Flipsky VX1:** Usa un receptor Flipsky VX1 conectado únicamente por UART (pin `S`/PPM vacío) que envía `COMM_SET_CHUCK_DATA` a ~100 Hz con 3 modos de potencia (**50% / 64% / 100%** acelerando; **100%** freno en los tres). El micro-USB del mando es **solo de carga**.
- **Misterio resuelto — Luces rojas parpadeando:** Mantener pulsado el botón izquierdo (~2 s) abre el **calibrador de celdas de batería del patín (`6S / 8S / 10S / 12S`)** para las 4 rayas centrales (leídas por el cable blanco `V`). **No cambia** potencia ni modos de asistencia. Para la batería ~24 V (7S) de AtmosGear, **2 LEDs (`8S`)** es el ajuste más práctico.
- **Origen del impulso automático al patinar:** Tras capturar 4.568 tramas UART en vivo (incluso simulando 5.000 ERPM desde una Raspberry Pi), se comprobó que el receptor envía **0** peticiones de RPM (`COMM_GET_VALUES`) y que `APPCONF` no tiene PAS activado: el impulso automático reside exclusivamente en el **firmware interno de los STM32F405**.

---

## Índice de Documentación

- **[Guía Técnica Completa en Español](docs/GUIA_COMPLETA_ES.md)** *(todo reunido en español)*
- [01 — Arquitectura de Hardware y Pinout](docs/01-hardware-architecture.md) *(EN)*
- [02 — Configuración de Fábrica VESC v5.02 (`MCCONF` y `APPCONF`)](docs/02-vesc-factory-configuration.md) *(EN)*
- [03 — Mando Remote AG1 / Flipsky VX1 y Protocolo UART](docs/03-remote-ag1-flipsky-vx1.md) *(EN)*
- [04 — Diagnóstico con Raspberry Pi y Puente Wi-Fi VESC Tool](docs/04-raspberry-pi-diagnostics-guide.md) *(EN)*
- [05 — Investigación del Impulso Automático al Patinar](docs/05-push-assist-investigation.md) *(EN)*
- [Backups binarios originales VESC v5.02](configs/README.md)
- [Herramientas Python (`decode_vesc_conf.py` y `analyze_flipsky.py`)](tools/README.md)

---

## Inicio Rápido con las Herramientas

```bash
# Ver diferencias exactas entre la APPCONF de fábrica de AtmosGear y VESC 5.02 estándar
python3 tools/decode_vesc_conf.py \
  configs/factory_vesc_5.02/default_appconf.bin \
  configs/factory_vesc_5.02/master_appconf.bin

# Analizar el receptor Flipsky VX1 desde una Raspberry Pi simulando 5000 ERPM
python3 tools/analyze_flipsky.py --port /dev/serial0 --duration 30 --fake-vesc --erpm 5000
```

---

## Aviso Legal y Contribuciones

Este es un proyecto comunitario **no oficial** e independiente, sin afiliación con AtmosGear ni Flipsky. Manipular baterías de litio, cableado o parámetros de controladoras VESC conlleva riesgos: **haz siempre copia de seguridad de tus propias controladoras antes de modificar nada**.

¡Pull Requests, fotos de la PCB, volcados y mejoras de la comunidad son bienvenidos!
