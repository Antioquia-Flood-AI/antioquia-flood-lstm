# 🧪 Bitácora de Experimentos — Fase 2 Inundaciones Antioquia

**Fecha:** 2 de junio de 2026  
**Propósito:** Documentar TODO lo que se intentó, lo que funcionó, lo que falló, y por qué. Para que futuros agentes IA (o humanos) no repitan los mismos errores.

---

## 1. Línea de Tiempo

```
Mayo 30    → Auditoría inicial del repositorio (~45 GB raw)
Mayo 31    → Primeros datasets y baselines LightGBM
Junio 1    → Descarga ERA5-Land 1981-2017 (Open-Meteo, 123 municipios)
           → Construcción dataset histórico, pelea con nulos (acentos, columnas duplicadas)
           → Extensión ERA5 a 2018-2025 (3 instancias Colab)
Junio 2 AM → Modelo DHIME real (AUROC 0.945), índices NOAA, LSTM, TIFFs, documentación
Junio 2 PM → Entrega final
```

---

## 2. Experimentos Realizados

### ✅ Experimento 1: LightGBM Baseline (Colab Optuna v2)
**Fecha:** Mayo 31  
**Dataset:** `dataset_fase2_con_niveles_target_combinado.parquet` (2018-2026)  
**Target:** `target_combinado`  
**Features:** 23 (precip acumulados, ONI, estáticas)  
**Resultado:** Test AUROC 0.718, Recall 0.052  

**Conclusión:** Pésimo. `fecha_mes` dominaba el feature importance (16%) porque el modelo usaba el año como proxy de patrones climáticos. Las features meteorológicas diarias solas no bastan.

---

### ✅ Experimento 2: Dataset Histórico ERA5-Land (1981-2017)
**Fecha:** Junio 1  
**Objetivo:** Extender el dataset a 1981 para usar más ground truth (1998+)  
**Método:** Descarga ERA5-Land diario para 123 municipios desde Open-Meteo API  
**Problemas encontrados:**
1. **42% de nulos** en el dataset construido
   - **Causa 1:** Acentos en nombres de municipios (Á vs A). El static file y ERA5 usaban codificaciones diferentes.
   - **Causa 2:** Columnas duplicadas (`elevacion_msnm_x`, `elevacion_msnm_y`) por merge de múltiples fuentes de estáticas.
   - **Causa 3:** 12 municipios sin datos de elevación en HydroATLAS.
2. **ET inflada:** El dataset "clásico" (2018+) tenía ET ~576 mm/mes (valor erróneo del pipeline anterior) vs ERA5 real ~101 mm/mes.

**Solución:** Unificar estáticas en `static_municipio_features.parquet`, imputar con mediana departamental, descargar ERA5 2018-2025 para tener ET consistente.  
**Descarga multi-cuenta:** 3 instancias de Colab, round-robin (41 municipios cada una), 6s delay entre requests.

**Resultado final:** Dataset 1981-2025 con ET consistente (0 nulos).  
**Pero:** Entrenar con ERA5 + `target_combinado` dio AUROC 0.717 — **igual que el baseline**. Extender el dataset hacia atrás no mejoró el modelo porque:
- ERA5 es peor que CHIRPS para precip. a escala municipal
- `target_combinado` es más ruidoso que `flood_target`
- Sin SAR ni TR scores para el período histórico

**Lección:** Más datos ≠ mejor modelo. La calidad de features > cantidad de datos.

---

### ✅ Experimento 3: Modelo DHIME Real (Game Changer)
**Fecha:** Junio 2 AM  
**Descubrimiento:** El archivo `dataset_fase2_con_dhime.parquet` YA tenía 63 features procesadas: CHIRPS, SAR, TR scores, Open-Meteo, topografía. **Habíamos estado reconstruyendo desde cero lo que ya existía.**

**Target:** `flood_target` (1,926 eventos, prevalencia 0.47%) — target más limpio y mejor distribuido temporalmente que `target_combinado`.

**Resultado:** Test AUROC **0.945**, F1 0.592, Recall 0.554.  
**Features #1:** `precip_acum_3d` (14.9%), `z_VV_mean` (7.8%), `precip_acum_7d` (6.3%). Sin dominancia de features temporales.

**Lección:** Revisar SIEMPRE los datos procesados antes de construir pipelines nuevos. El dataset ya estaba casi listo.

---

### ❌ Experimento 4: Extensión a 1998 con target_combinado
**Fecha:** Junio 2 AM  
**Objetivo:** Usar los 5,164 eventos de `target_combinado` (1998-2025) para entrenar con más ground truth.  
**Método:** Construir dataset con ERA5 + estáticas del DHIME + `target_combinado`.

**Resultado:** Test Recall **0.000**. El modelo no detectó NINGUNA inundación.  
**Causa:** `target_combinado` (0.26% prevalencia) es más ruidoso. Sin CHIRPS ni SAR, las features de ERA5 no tienen suficiente señal.

**Lección:** `flood_target` > `target_combinado` como target. Calidad de target > cantidad de target.

---

### ✅ Experimento 5: Índices NOAA (SOI, QBO, Niño regions)
**Fecha:** Junio 2 AM  
**Objetivo:** Agregar índices climáticos más allá de ONI.  
**Fuente:** `raw/indices_noaa/indices_climaticos_mensuales.parquet` (22 índices, 2018-2025).

**Features agregadas:** SOI, QBO30, QBO50, ZWND200, N12_ANOM, N3_ANOM, N4_ANOM (7 nuevas, 0% NaN).

**Resultado:**
- AUROC: 0.942 → **0.946** (+0.004)
- Recall: 0.470 → **0.561** (+0.091)
- Los índices NOAA aportaron 11.6% del peso total
- QBO50 (2.2%) superó a ONI (1.7%) en importancia

**Lección:** Los índices climáticos de gran escala SÍ ayudan a predecir inundaciones. La QBO es particularmente relevante para Colombia. El archivo `indices_climaticos_mensuales.parquet` es oro.

---

### ❌ Experimento 6: LSTM (CPU local)
**Fecha:** Junio 2 AM  
**Objetivo:** Modelo secuencial que capture patrones temporales.  
**Arquitectura:** LSTM(52→128→64→1), 2 capas, dropout 0.3, 15 días de contexto.

**Resultado:** Timeout a los 15 minutos en CPU. No terminó de entrenar.

---

### ❌ Experimento 7: LSTM (Colab GPU)
**Fecha:** Junio 2 AM  
**Objetivo:** Reintentar LSTM con GPU de Colab.  
**Dataset exportado:** `exportar_colab_lstm/dataset_lstm.parquet` (52 features, 408K filas).

**Resultado:**
- Val F1: 0.0135, AUROC: 0.510 (¡aleatorio!)
- Test AUROC: 0.559, F1: 0.014
- Ensemble LSTM+LightGBM: AUROC 0.895 (peor que LightGBM solo, 0.946)

**Causa del fracaso:**
1. Prevalencia bajísima (0.47%) — el LSTM no tiene suficiente señal en secuencias de 15 días
2. Features tabulares municipio×día no tienen suficiente estructura temporal para que el LSTM encuentre patrones
3. El LightGBM ya captura las interacciones no lineales mejor que el LSTM para este tipo de datos

**Lección:** LSTM no es superior a LightGBM para datos tabulares con baja prevalencia. El LSTM brilla con secuencias ricas (píxeles, series de tiempo multivariadas densas), no con features ingeniería-das.

---

### ⚠️ Experimento 8: Cascada Stage1→Stage2 (Paranoico + LSTM)
**Fecha:** Junio 2  
**Descubrimiento:** Los modelos `lgb_stage1_paranoico.txt` y `lstm_stage2_best.pt` en `models/fase2/` formaban una cascada diseñada previamente:
- Stage 1: LightGBM con umbral 0.0024 (altísimo recall)
- Stage 2: LSTM que validaba candidatos

**Problema:** Features incompatibles. El stage1 paranoico usa 48 features con nombres distintos (`elevacion_msnm_x`, `nivel_instantaneo_mean`, `tiene_gauge`, flags `_missing`). Solo 14/48 coinciden con nuestro dataset DHIME.

**Resultado:** No se pudo hacer ensemble. Los modelos fueron entrenados en versiones diferentes del dataset.

**Lección:** Versionar los datasets y documentar las columnas. La compatibilidad entre modelos depende de features idénticas.

---

### ⚠️ Experimento 9: Umbral por Municipio
**Fecha:** Junio 2  
**Objetivo:** Calibrar thresholds individuales para los 8 municipios con 0% recall.

**Método:** Calcular umbral óptimo (max F1) por municipio en validación.

**Resultado:**
- Sin restricción: +13 FN recuperados, pero FP explotó de 95 a 685. Precision: 0.63 → 0.20.
- Con restricción (solo bajar umbral en municipios problemáticos): +2 FN recuperados.

**Causa:** Los municipios con 0 recall tienen pocas instancias en validación. Los umbrales "óptimos" sobreajustan.

---

### ❌ Experimento 10: Filtro Físico (Cascada Stage 2)
**Fecha:** Junio 2  
**Objetivo:** Post-procesar predicciones del LightGBM con reglas físicas para eliminar falsos positivos.

**Reglas probadas:**
- Sin lluvia reciente (`precip_acum_7d < 3mm`) → no inundación
- El Niño + mes seco → no inundación
- `pct_inundable < 0.01%` → no inundación

**Resultado:** 0 FP eliminados, 5 TP perdidos. El LightGBM ya codifica estas reglas en sus árboles.

---

### 🔮 Experimento 11: TIFFs SAR para ConvLSTM (Exploratorio)
**Fecha:** Junio 2  
**Archivos:** 9,487 tiles en `/content/drive/MyDrive/GEE_ConvLSTM_Antioquia/`  
**Formato:** 65×65 píxeles × 5 bandas (VV_post_db, VH_post_db, slope, elevation, flood_gt)  
**Cobertura:** 27 de 100 puntos objetivo, 548 fechas (cada 6 días, 2018-2026)

**Problema:** 60% NaN en los tiles. La lectura secuencial desde Drive toma ~47 minutos para los 9,487 archivos.

**Potencial:** Si se completa la extracción de los 100 puntos y se manejan los NaN (interpolación temporal, descarte de tiles vacíos), estos datos son **ideales para ConvLSTM** en Fase 3:
- Ground truth a nivel píxel (`flood_gt`)
- Series temporales de SAR (cada 6 días)
- Contexto topográfico (slope, elevation)

**Estado:** Trabajo futuro. No viable para Fase 2.

---

## 3. Resumen de Errores y Lecciones

| # | Error | Causa | Lección |
|---|-------|-------|---------|
| 1 | 42% nulos en dataset ERA5 | Acentos, columnas duplicadas, datos faltantes | Normalizar strings ANTES de merge. Usar fuente única de estáticas. |
| 2 | Extender dataset a 1981 no mejoró el modelo | ERA5 < CHIRPS, target ruidoso | Calidad de features > cantidad de datos |
| 3 | Reconstruir pipeline que ya existía | No revisar `processed/fase2/` | **Siempre auditar datos procesados primero** |
| 4 | `target_combinado` vs `flood_target` | Targets diferentes sin documentar | Documentar definición de cada target |
| 5 | LSTM peor que LightGBM | Datos tabulares, baja prevalencia | No forzar DL donde ML clásico funciona |
| 6 | Ensemble con modelos viejos | Features incompatibles | Versionar datasets y columnas |
| 7 | Umbral por municipio | Sobreajuste en validación | Mínimo 20+ positivos por grupo para calibrar |
| 8 | TIFFs desde Drive muy lentos | 9,487 archivos × latencia de red | Procesar TIFFs localmente o en GEE, no desde Drive |

---

## 4. Lo Que Sí Funcionó

| Técnica | Impacto |
|---------|:-------:|
| LightGBM + class_weight='balanced' | Base sólida |
| CHIRPS en vez de ERA5 | +0.23 AUROC |
| SAR features (VV, VH, z_VV) | 20% de importancia |
| Índices NOAA (SOI, QBO, Niño regions) | +9% recall |
| TR scores como features estáticas | +0.7% AUROC |
| Split temporal estricto (sin shuffle) | Evitó fuga temporal |
| pct_inundable (susceptibilidad) | Feature complementaria útil |

---

## 5. Comparativa de Todos los Modelos

**Métricas en Test (≥2025)** salvo que se indique lo contrario.

| # | Modelo | Target | Período | Feats | AUROC | F1 | Recall | Prec | Estado |
|:-:|--------|--------|---------|:-----:|:-----:|:---:|:------:|:----:|--------|
| 1 | `lgbm_dhime_con_indices_noaa.txt` | `flood_target` | 2018–2026 | 52 | **0.946** | **0.593** | **0.561** | 0.628 | ⭐ **GANADOR** |
| 2 | `lgbm_dhime_pulido_final.txt` | `flood_target` | 2018–2026 | 45 | 0.942 | 0.562 | 0.470 | 0.698 | Pulido sin NOAA |
| 3 | `lgbm_dhime_real_backup.txt` | `flood_target` | 2018–2026 | 43 | 0.945 | 0.562 | 0.554 | ~0.57 | Backup DHIME base |
| 4 | `lgbm_target-combinado_1998-2025.txt` | `target_combinado` | 1998–2025 | 36 | 0.717 | 0.000 | 0.000 | 0.000 | ❌ Sin CHIRPS/SAR |
| 5 | `lightgbm_1981_2025_v3.txt` | `target_combinado` | 1981–2025 | 23 | 0.760 | 0.027 | 0.052 | 0.018 | ❌ ET inconsistente |
| 6 | `lstm_flood_best.pt` | `flood_target` | 2018–2026 | 52 | 0.559 | 0.014 | 0.095 | 0.008 | ❌ LSTM fracasó |

**Observaciones:**
- **Modelos 1-3** usan `flood_target` (DAGRAN, 1,926 eventos, prevalencia 0.47%) y CHIRPS + SAR. Son los que funcionan.
- **Modelos 4-5** usan `target_combinado` (DAGRAN+UNGRD, 5,164 eventos, prevalencia 0.26%) y ERA5. El target más ruidoso y la peor precipitación los hunden.
- **Modelo 6** (LSTM) fracasa porque 15 días de contexto tabular no aportan señal adicional sobre lo que LightGBM ya captura con features de ingeniería.
- **Diferencia #1 vs #4:** +0.229 AUROC. Esto es CHIRPS+SAR vs ERA5 solo. La fuente de precipitación es el factor determinante.

---

## 6. Ficha Técnica — Modelo Ganador 🏆

### Identificación
| Campo | Valor |
|-------|-------|
| **Nombre** | `lgbm_dhime_con_indices_noaa.txt` |
| **Algoritmo** | LightGBM (Gradient Boosting Decision Trees) |
| **Hiperparámetros** | Optimizados vía Optuna: 250 trials, TPE sampler, seed=42 |
| **Versión LightGBM** | 4.x |
| **Tamaño del archivo** | ~13 MB |

### Datos de Entrenamiento
| Campo | Valor |
|-------|-------|
| **Dataset** | `dataset_fase2_con_dhime.parquet` + NOAA + pct_inundable + river_density |
| **Filas totales** | 408,443 |
| **Municipios** | 123 |
| **Período** | 2018-01-01 → 2026-05-29 |
| **Target** | `flood_target` (1,926 positivos, 0.47% prevalencia) |
| **Features** | 52 (ver sección 4 del INFORME_MODELO.md) |

### Split y Validación
| Campo | Valor |
|-------|-------|
| **Estrategia** | Split temporal estricto (sin shuffle) |
| **Train** | ≤ 2023-12-31 (291,403 filas, 1,463 positivos) |
| **Val** | 2024-01-01 → 2024-12-31 (48,678 filas, 178 positivos) |
| **Test** | ≥ 2025-01-01 (68,362 filas, 285 positivos) |
| **Validación cruzada** | No (serie temporal) |

### Rendimiento en Test
| Métrica | Valor | Interpretación |
|---------|:-----:|----------------|
| **AUROC** | 0.9458 | Excelente capacidad de ranking |
| **AUPRC** | 0.5386 | Bueno considerando prevalencia 0.47% |
| **F1-Score** | 0.5926 | Balance precisión-recall |
| **Recall** | 0.5614 | Detecta 56 de cada 100 inundaciones |
| **Precision** | 0.6275 | 63% de las alertas son inundaciones reales |
| **Accuracy** | 0.9969 | 99.7% (dominada por clase negativa) |
| **True Positives** | 160 | Inundaciones correctamente detectadas |
| **False Positives** | 95 | Falsas alarmas (0.14% de días sin inundación) |
| **False Negatives** | 125 | Inundaciones no detectadas |
| **Umbral óptimo** | ~0.25 | Maximiza F1 en validación |

### Categorías de Features y su Peso
| Categoría | Peso | Features clave |
|-----------|:----:|----------------|
| Precipitación (CHIRPS) | 39.3% | `precip_acum_3d` (14.1%), `precip_acum_7d` (6.6%) |
| SAR (Sentinel-1) | 20.2% | `z_VV_mean` (8.0%), `VH_mean` (4.1%) |
| Topografía | 14.6% | `twi_max`, `slope_p90`, `acc_mean` |
| Índices NOAA | 11.6% | `oni_anom` (3.3%), `QBO50` (2.2%), `SOI` (1.2%) |
| Humedad/Viento | 7.4% | `humedad_media` (3.8%), `viento_medio` (3.7%) |
| Temperatura | 5.8% | `temperatura_media` (3.0%) |
| Ríos/Drenaje | 5.6% | `distancia_rio_km_real`, `river_length_km` |

### Ecuaciones Relevantes
Las features de precipitación acumulada se calculan como:
- `precip_acum_3d = Σ(precip_día[t-2], precip_día[t-1], precip_día[t])`
- `precip_acum_7d = Σ(t-6 ... t)`
- `precip_acum_15d = Σ(t-14 ... t)`
- `precip_acum_30d = Σ(t-29 ... t)`

Los índices NOAA se mergean por año-mes (ej: `oni_anom` de marzo 2025 se asigna a todos los días de marzo 2025).

### Cómo Cargar y Usar el Modelo
```python
import lightgbm as lgb
import pandas as pd

# Cargar modelo
model = lgb.Booster(model_file='lgbm_dhime_con_indices_noaa.txt')

# Cargar datos (deben tener las 52 features en el mismo orden)
df = pd.read_parquet('dataset_fase2_con_dhime.parquet')
# ... agregar índices NOAA, pct_inundable, river_density ...

# Predecir
features = model.feature_name()  # 52 features
probabilidades = model.predict(df[features])

# Clasificar con umbral 0.25
predicciones = (probabilidades >= 0.25).astype(int)
```
