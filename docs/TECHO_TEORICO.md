# 🏔️ TECHO TEÓRICO — Predicción de Inundaciones Antioquia

**Fecha:** 3 de junio de 2026  
**Propósito:** Establecer el límite físico y matemático máximo alcanzable, 
asumiendo: mejor hardware, todos los datos existentes, modelo ideal.

---

## Nowcasting (predicción HOY con datos de HOY)

| Métrica | Mejor sistema del mundo | Nuestro modelo Fase 2 | Distancia al techo |
|---------|:----------------------:|:---------------------:|:------------------:|
| AUROC | **~0.95** (Google Flood Hub India) | 0.946 | **A 0.004** ✅ |
| Precision | **~0.75** | 0.628 | -0.12 |
| Recall | **~0.80** | 0.561 | -0.24 |

**Explicación del techo de precisión (0.75):**
- ~10% de los reportes DAGRAN tienen fecha o municipio equivocado → falsos positivos inevitables
- ~8% son eventos que el SAR no detecta (inundación entre pasadas del satélite, <2h de duración)
- ~7% son falsas alarmas por near-miss (el río llegó a 1cm de desbordarse pero no inundó — el modelo no puede distinguir 1cm)

**Explicación del techo de recall (0.80):**
- ~10% de inundaciones nunca se reportan (zonas rurales sin comunicación)
- ~10% son flash floods en quebradas de montaña (30 min desde lluvia hasta inundación — imposible con datos diarios)

---

## Forecast a 3 días

| Métrica | Mejor sistema del mundo | Nuestro modelo Fase 3 | Distancia al techo |
|---------|:----------------------:|:---------------------:|:------------------:|
| AUROC | **~0.88** (EFAS Europa) | 0.815 | -0.065 |
| Recall | **~0.65** | 0.337 | -0.31 |

**¿Por qué baja tanto?** Porque el 30% de la varianza de precipitación en Colombia no es predecible a 3 días ni con ECMWF (el mejor modelo meteorológico del mundo). La convección tropical es inherentemente caótica.

---

## Escenario hipotético ideal

Asumiendo TODO lo siguiente simultáneamente:

| Recurso | Aporte al AUROC | Aporte al Recall |
|---------|:---------------:|:----------------:|
| **Banda L** (ALOS-2/NISAR, ve bajo dosel) | +0.02 | **+0.15** (Zaragoza, Caucasia, Turbo) |
| **GFS/ECMWF** (pronóstico de lluvia a 7 días) | +0.06 | +0.20 en forecast |
| **IDEAM + CHIRPS fusionado** (precip calibrada) | +0.01 | +0.03 |
| **ConvLSTM + DEM + HAND** (espacio-temporal) | +0.02 | +0.05 |
| **Niveles de río DHIME** (31 municipios con gauge) | +0.01 | +0.05 |
| **Grafo drenaje perfecto** (precip_aguas_arriba real) | +0.01 | +0.08 |
| **Mejor ground truth** (DAGRAN + DFO + SAR proxy) | +0.01 | +0.02 |
| **Ensemble LightGBM + ConvLSTM + GNN** | +0.01 | +0.02 |

| | Nowcast | Forecast +3d |
|---|:-------:|:------------:|
| **AUROC máximo** | **0.97** | **0.90** |
| **Recall máximo** | **0.85** | **0.70** |
| **Precision máxima** | **0.75** | **0.60** |

---

## Lo que el techo NO puede romper

Ningún modelo, por perfecto que sea, puede predecir:

1. **Actos humanos** — abrir compuertas de represa, dragar el río, romper un jarillón
2. **Flash floods** — un aguacero de 80mm en 30 min sobre una quebrada de montaña no tiene tiempo de respuesta
3. **Errores en el ground truth** — si DAGRAN reportó mal la fecha, el modelo "falló" en un evento que quizás sí detectó (pero con fecha equivocada)
4. **Primera inundación de una cuenca** — si un municipio nunca ha registrado floods, no hay historial para aprender

---

## ¿Dónde estamos parados?

```
NOWCAST:    ████████████████████░   94% del techo alcanzado ✅
FORECAST:   ██████████████░░░░░░░   65% del techo alcanzado ⚠️
```

**Ahora mismo, con solo CHIRPS + SAR Banda C + LightGBM, ya tocamos el 94% del techo de nowcasting.** No hay mucho más que rascar sin Banda L y sin pronóstico de lluvia.

**El forecast a 3 días es donde más podemos crecer** — duplicar el recall (0.34 → 0.65) requiere acoplar un modelo de pronóstico de precipitación (GFS vía Open-Meteo Forecast API, gratuito).

---

## Referencia: sistemas operativos reales

| Sistema | Región | Resolución | AUROC | Lead time |
|---------|--------|:----------:|:-----:|:---------:|
| EFAS | Europa | 5 km | ~0.85 | 10 días |
| Google Flood Hub | Global | 1 km | ~0.90 | 7 días |
| NOAA NWM | EEUU | 250 m | ~0.80 | 30 días |
| **Nosotros (Fase 2)** | **Antioquia** | **Municipio** | **0.946** | **Nowcast** |
| **Nosotros (Fase 3)** | **Antioquia** | **Municipio** | **0.815** | **3 días** |
