# Bitácora del Grupo 6 (S5 BFSK)

| Fecha | Actividad | Decisión / resultado |
|---|---|---|
| 08/10/2026 | Lectura de la guía del proyecto y elección del escenario S5. | Telemetría binaria con BFSK; variable principal Δf. |
| 15/10/2026 | Ficha de decisión técnica ciega. | Paquete A (Rs = 32 kBd, SPS = 8, fs = 256 kS/s), perturbación AWGN, hipótesis H1. |
| 15/10/2026 | Retroalimentación de la ficha: «TODAVÍA NO VIABLE» (inconsistencia Rs–SPS–fs; la perturbación no representa el fenómeno). | El docente indicó corregir los valores a criterio del grupo, sin reenviar la ficha. |
| Guía 2 | Primera versión del sistema con el paquete A (256 kS/s, sps = 8, Δf = 8 a 32 kHz). | Funcionaba, pero cambiaba la tasa del GRC base: era justamente la inconsistencia señalada. |
| Guía 2 | Primer receptor: discriminador + integrador + Keep 1 in N + slicer. | **Prueba fallida:** sin filtro de canal el discriminador recibía todo el ruido. Se agregó un FIR de canal con corte Δf + Rs/2. |
| Guía 2 | **Prueba fallida:** la fase de muestreo fija quedaba corrida. | Se reemplazó Keep 1 in N por Symbol Sync (Gardner). |
| 05/11/2026 | Práctica HackRF One en el laboratorio (16-QAM del curso, Grupo 6 como transmisor). | Se validaron Osmocom Sink y lo_off = 200 kHz. Se observaron el pico de DC, el offset entre radios y la pérdida de sincronía. |
| 05/11/2026 | El medidor del Rx marcó BER ≈ 18 % con CRC = OK. | Diagnóstico: referencia desalineada o ambigüedad de fase. Lección para la medición BER. |
| Guía 4 | Integración de e_EbN0_Sweep y e_BER_Curve. | **Prueba fallida:** con loop_bw = 0,045 el sincronizador deslizaba bits. Se pasó a 0,005 y se creó e_PRBS_Ref con reenganche. |
| 11/11/2026 | **Corrección de la decisión técnica** con la plataforma de decisión ciega y el selector guiado. | Paquete C (Rs = 10 kBd, SPS = 100, fs = 1 MS/s), perturbación «Variar Δf», GRC base Modulacion_FSK_AWGN.grc. |
| 11/11/2026 | Pruebas del selector: ref (5 kHz, 0), suave (5 kHz, 0,05), media (10 kHz, 0,10), fuerte (20 kHz, 0,20). | BW99 = 21,4 / 33,4 / 56,8 kHz; 0 errores en las cuatro pruebas. |
| 11/11/2026 | Receptor adaptado: el filtro de canal decima ×10 (100 kS/s, 10 muestras/símbolo). | Receptor 10 veces más liviano; la discriminación sobre la señal filtrada queda limpia. |
| 11/11/2026 | Hardware: resampler 2/1 (Tx) y 1/2 (Rx). Prueba en lazo con offset. | Con 5 kHz de offset solo funciona con DC Blocker; con 10 kHz hay que corregir con rx_ppm ≈ 10 ppm. |
| 11/11/2026 | Curvas BER para Δf = 5, 10 y 20 kHz (50 000 bits por punto). | Eb/N0 @ 10⁻³: 11,1 / 13,6 / 13,9 dB. |

## Dificultades y cómo se resolvieron
- Parámetros incoherentes con el GRC base → se adoptó el paquete C del escenario.
- Ruido fuera de banda en el discriminador → filtro de canal ajustado a Carson.
- Fase de muestreo desconocida → sincronizador de Gardner.
- Tx y Rx en computadores distintos → PRBS9 conocida y alineación automática.
- Offset de frecuencia entre HackRF → DC Blocker, medidor de offset y corrección en ppm.
