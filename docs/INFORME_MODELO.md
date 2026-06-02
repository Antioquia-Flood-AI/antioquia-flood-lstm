# 🌊 Modelo de Predicción de Inundaciones — Antioquia Fase 2

**Fecha:** 2 de junio de 2026  
**Autores:** Equipo Antioquia Flood Prediction  
**Archivo del modelo:** `FloodAntioquia/models/lgbm_dhime_con_indices_noaa.txt`

---

## 1. Resumen Ejecutivo

Se desarrolló un modelo **LightGBM** para predicción binaria de inundaciones a nivel **municipio × día** en los 123 municipios de Antioquia. El modelo alcanza un **AUROC de 0.946** en test (años 2025+), con una tasa de detección del 56% y una precisión del 63%.

El modelo utiliza 52 features organizadas en 5 categorías: precipitación (CHIRPS), radar satelital (SAR Sentinel-1), índices climáticos (NOAA), topografía y susceptibilidad de inundación.

---

## 2. Métricas

| Split | Período | Filas | Positivos | AUROC | F1 | Recall | Precision | TP | FP |
|-------|---------|------:|----------:|:-----:|:---:|:------:|:---------:|---:|---:|
| Train | ≤2023 | 291,403 | 1,463 (0.50%) | 0.9997 | 0.719 | 0.569 | 0.977 | 833 | 20 |
| Val | 2024 | 48,678 | 178 (0.37%) | 0.9633 | 0.796 | 0.680 | 0.960 | 121 | 5 |
| **Test** | **≥2025** | **68,362** | **285 (0.42%)** | **0.9422** | **0.562** | **0.470** | **0.698** | **134** | **58** |

**Interpretación del test:**
- El modelo detecta 134 de 285 inundaciones reales (47% recall)
- De cada 100 alertas emitidas, ~70 son inundaciones reales (70% precisión)
- Solo 58 falsas alarmas en 68,362 días-municipio (0.08% de los días)
- **Accuracy global: 99.7%** (dominada por la clase negativa, como es esperable en eventos raros)

### Versión con índices NOAA (modelo final)

| Split | AUROC | F1 | Recall | Precision |
|-------|:-----:|:---:|:------:|:---------:|
| **Test** | **0.9458** | **0.593** | **0.561** | **0.628** |

Los índices NOAA (SOI, QBO30, QBO50, ZWND200, N12_ANOM, N3_ANOM, N4_ANOM) aportaron **+9 puntos de recall** y **11.6% del peso total** de features.

---

## 3. Arquitectura del Modelo

### Algoritmo
**LightGBM** (Gradient Boosting Decision Trees) con los siguientes hiperparámetros optimizados vía Optuna (250 trials):

| Parámetro | Valor |
|-----------|-------|
| learning_rate | 0.0060 |
| num_leaves | 251 |
| max_depth | 7 |
| min_child_samples | 46 |
| subsample | 0.332 |
| colsample_bytree | 0.391 |
| reg_alpha | 0.030 |
| reg_lambda | 0.012 |
| class_weight | balanced |
| n_estimators | 1,449 |

### Split temporal estricto
- **Train:** 2018-01-01 → 2023-12-31
- **Val:** 2024-01-01 → 2024-12-31
- **Test:** 2025-01-01 → 2026-05-29
- **Sin aleatoriedad:** split puramente cronológico para evitar fuga temporal

### Target
`flood_target`: variable binaria derivada de reportes DAGRAN y UNGRD. 1,926 eventos en el dataset completo (prevalencia 0.47%). Incluye eventos de inundación, deslizamiento por lluvia, y crecientes súbitas.

---

## 4. Features (52 columnas)

### 4.1 Precipitación (CHIRPS) — 39.3% de importancia
| Feature | Importancia |
|---------|:----------:|
| `precip_acum_3d` | 14.1% |
| `precip_acum_7d` | 6.6% |
| `precip_acum_30d` | 4.7% |
| `precip_acum_15d` | 4.6% |
| `chirps_precip_mm_dia` | 4.3% |
| `precip_acum_1d` | 2.7% |
| `p90_precip_3d` | 2.3% |

### 4.2 SAR Sentinel-1 — 20.2% de importancia
| Feature | Importancia |
|---------|:----------:|
| `z_VV_mean` | 8.0% |
| `VH_mean` | 4.1% |
| `VV_mean` | 3.3% |
| `VV_minus_VH` | 2.8% |
| `n_scenes` | 2.1% |

### 4.3 Índices climáticos NOAA — 11.6% de importancia
| Feature | Importancia | Descripción |
|---------|:----------:|-------------|
| `oni_anom` | 3.3% | Oceanic Niño Index (anomalía) |
| `oni_total` | 3.1% | Oceanic Niño Index (valor) |
| `QBO50` | 2.2% | Oscilación Cuasi-Bienal a 50hPa |
| `ZWND200` | 1.8% | Viento zonal a 200hPa |
| `N12_ANOM` | 1.7% | Anomalía Niño 1+2 |
| `SOI` | 1.2% | Southern Oscillation Index |
| `N3_ANOM`, `N4_ANOM` | <1% | Niño 3 y 4 |
| `QBO30` | <1% | Oscilación Cuasi-Bienal a 30hPa |

### 4.4 Topografía y susceptibilidad
| Feature | Importancia |
|---------|:----------:|
| `distancia_rio_km_real` | 1.5% |
| `pendiente_val` | 1.3% |
| `elevacion_msnm` | <1% |
| `slope_mean`, `twi_mean`, `acc_mean` | <1% c/u |
| `pct_inundable` | <1% |
| `river_length_km`, `river_density_km_per_km2` | <1% c/u |

### 4.5 Variables atmosféricas (Open-Meteo)
| Feature | Importancia |
|---------|:----------:|
| `humedad_media` | 3.8% |
| `viento_medio` | 3.7% |
| `temperatura_media` | 3.0% |
| `temperatura_max` | 2.9% |

---

## 5. Distribución de Feature Importance

```
Precipitación (CHIRPS)  ████████████████████ 39.3%
SAR (Sentinel-1)        ██████████ 20.2%
Topografía              ███████ 14.6%
Índices NOAA            ██████ 11.6%
Humedad/Viento          ████ 7.4%
Temperatura             ███ 5.8%
Ríos/Drenaje            ██ 5.6%
Amenaza (TR)            █ 0.7%
```

La distribución es **saludable**: ninguna feature domina, el modelo usa información de múltiples fuentes.

---

## 6. Limitaciones

1. **Heterogeneidad espacial:** 8 municipios (Zaragoza, Arboletes, Carepa, Caucasia, Rionegro, Turbo, Urrao, Venecia) tienen **0% recall** en test. Inundan con mucha menos lluvia local — posiblemente por causas aguas arriba o saturacion del suelo. El modelo global no captura sus particularidades.

2. **Prevalencia baja (0.47%):** El desbalance de clases limita el recall. Estrategias de muestreo (SMOTE, undersampling) no mejoraron los resultados significativamente.

3. **Cobertura temporal limitada:** El dataset solo cubre 2018-2026. La extensión a 1998-2017 con ERA5-Land no mejoró el rendimiento (AUROC 0.717) porque CHIRPS y SAR no están disponibles para ese período.

4. **Sin datos de niveles de río en la mayoría de municipios:** Solo 31 de 123 municipios tienen estaciones de medición (DHIME). Para los 92 restantes, estas features son 0.

---

## 7. Trabajo Futuro

1. **ConvLSTM con tiles SAR:** 9,487 tiles de 65×65 píxeles con 5 bandas (VV, VH, slope, elevation, flood_gt) ya están generados para 27 de 100 puntos. Completar la extracción y entrenar un modelo espaciotemporal que capture patrones de inundación a nivel píxel.

2. **Modelos por cuenca hidrográfica:** Agrupar municipios por cuenca (usando `antioquia_drenaje_sencillo.geojson`) y entrenar modelos especializados por región.

3. **Integración de niveles de río (DHIME):** Para los 31 municipios con estaciones, los niveles de río mostraron señal fuerte (+24m en días de inundación). Un modelo específico para estos municipios podría alcanzar recall >70%.

4. **Ground truth satelital (DFO):** El archivo `dfo_ground_truth_candidates.csv` contiene 119 eventos adicionales del Dartmouth Flood Observatory que podrían aumentar el dataset de entrenamiento.

---

## 8. Archivos Entregables

### Principal (obligatorio)
| Archivo | Descripción |
|---------|-------------|
| `FloodAntioquia/models/lgbm_dhime_con_indices_noaa.txt` | ⭐ **Modelo final** (52 features). Cargar con `lightgbm.Booster(model_file=...)` |
| `processed/fase2/dataset_fase2_con_dhime.parquet` | Dataset de entrenamiento (408K filas, 2018-2026) |

### Complementarios
| Archivo | Descripción |
|---------|-------------|
| `FloodAntioquia/models/lgbm_dhime_real_backup.txt` | Modelo backup sin índices NOAA (45 features) |
| `docs/INFORME_MODELO.md` | Este informe |
| `docs/DATOS_Y_FUENTES.md` | Catálogo completo de fuentes y procesamiento |
| `docs/BITACORA_EXPERIMENTOS.md` | Historial de experimentos, errores y lecciones |
