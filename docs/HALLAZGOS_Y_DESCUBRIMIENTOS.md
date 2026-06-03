# 🏆 HALLAZGOS Y DESCUBRIMIENTOS — Proyecto Antioquia Flood Prediction

**Versión:** 3 de junio de 2026 (incluye análisis post-entrega)
**Propósito:** Síntesis de todo lo descubierto en Fase 2 y la exploración post-entrega.

---

## 1. Lo Que Funcionó ✅

### 1.1 CHIRPS es el mejor dato de precipitación disponible

| Fuente | AUROC con ese dato |
|--------|:------------------:|
| **CHIRPS (~5 km)** | 0.946 |
| ERA5-Land (~9 km) | 0.717 |

CHIRPS combina satélite infrarrojo con calibración de estaciones terrestres. ERA5 es puramente modelado. La diferencia de **+0.229 AUROC** es abismal. Descargar ERA5-Land para 1981-2025 (123 municipios, 3 instancias Colab) tomó 2 días y NO mejoró el modelo, porque la calidad del dato —no la cantidad— es lo que importa.

### 1.2 Las features SAR son imprescindibles (20% del peso total)

`z_VV_mean` (8.0%), `VH_mean` (4.1%), `VV_mean` (3.3%) y `VV_minus_VH` (2.8%) son features #2, #7, #10 y #15 del modelo. El radar ve agua en superficie y es el segundo predictor más importante después de la precipitación.

### 1.3 Los índices NOAA suman 11.6% y suben el recall +9 puntos

SOI, QBO30/50, ZWND200, N12/3/4_ANOM fueron agregados en el último día de Fase 2. La QBO50 (oscilación cuasi-bienal) resultó más importante que el ONI (2.2% vs 1.7%). Los índices climáticos de gran escala SÍ predicen inundaciones en Colombia.

### 1.4 El dataset ya existía (y nadie lo sabía)

El archivo `dataset_fase2_con_dhime.parquet` (408K filas, 63 features) ya estaba procesado con CHIRPS, SAR, TR scores, Open-Meteo y topografía. Pasamos 2 días reconstruyendo pipelines desde cero cuando la solución estaba en `processed/fase2/`. **Lección: auditar SIEMPRE los datos procesados antes de construir.**

### 1.5 `flood_target` > `target_combinado`

Dos definiciones de ground truth en el repositorio:
- `flood_target`: 1,926 eventos, 0.47% prevalencia, bien distribuido temporalmente → AUROC 0.946
- `target_combinado`: 5,164 eventos, 0.26% prevalencia, más ruidoso → AUROC 0.717

**Más eventos no es mejor si el target es ruidoso.** El target de DAGRAN (`flood_target`) es superior al combinado DAGRAN+UNGRD.

### 1.6 Split temporal estricto sin shuffle

Sin validación cruzada aleatoria. Train ≤ 2023, Val = 2024, Test ≥ 2025. Esto evitó fugas temporales que habrían inflado artificialmente las métricas. El modelo predice el futuro con datos del pasado — como debe ser.

---

## 2. Lo Que Falló ❌

### 2.1 Extender el dataset a 1998-2017 con ERA5

**Intento:** Descargar ERA5-Land 1981-2025 para 123 municipios y usar los 5,164 eventos históricos de `target_combinado`.

**Resultado:** AUROC 0.717, Recall 0.000. El modelo no detectó NINGUNA inundación.

**Por qué falló:** ERA5 es ~9 km, solo modelo. CHIRPS es ~5 km, calibrado con estaciones. Y `target_combinado` es más ruidoso. Calidad de datos > cantidad de datos.

### 2.2 LSTM para datos tabulares

**Intento:** LSTM (52→128→64→1) con secuencias de 15 días, entrenado en Colab GPU.

**Resultado:** AUROC 0.559, F1 0.014. Básicamente aleatorio. Peor que LightGBM por 0.387 AUROC.

**Por qué falló:** Prevalencia 0.47% + features tabulares. El LSTM no encuentra patrones secuenciales en datos municipio×día. Brilla con píxeles (ConvLSTM), no con tablas.

### 2.3 Ensemble con modelos viejos (Paranoico + Stage2 LSTM)

**Intento:** Usar la cascada `lgb_stage1_paranoico.txt` + `lstm_stage2_best.pt` que ya existía en `models/fase2/`.

**Resultado:** Imposible. Solo 14/48 features coincidían. Los modelos viejos fueron entrenados con columnas distintas (`elevacion_msnm_x`, flags `_missing`, `nivel_instantaneo_mean`).

**Lección:** Versionar datasets y documentar columnas. Sin compatibilidad de features, los modelos son inservibles.

### 2.4 Filtro físico (cascada Stage 2 con reglas)

**Intento:** Post-procesar predicciones con reglas: "sin lluvia reciente → no flood", "El Niño + mes seco → no flood".

**Resultado:** 0 FP eliminados, 5 TP perdidos. LightGBM ya codifica esas reglas en sus árboles mejor que cualquier heurística manual.

### 2.5 `precip_aguas_arriba` con grafo de drenaje

**Intento:** Construir grafo dirigido de conectividad hidrológica con `antioquia_drenaje_sencillo.geojson` (30,732 segmentos) y calcular precipitación de municipios aguas arriba para los 8 que fallan.

**Resultado:** La feature tuvo **0.0% de importancia** (puesto #58 de 58).

**Por qué falló:** El DEM de 250m es muy grueso. Los 30K segmentos finos caen en los mismos píxeles → elevación idéntica → 631 aristas descartadas. Para un grafo correcto se necesita el DEM de 30m con algoritmo D8 de dirección de flujo.

---

## 3. Los Grandes Descubrimientos 🔬

### 3.1 La Hipótesis de los Dos Regímenes de Inundación

El hallazgo más importante de todo el proyecto. **Antioquia sufre de dos tipos de inundación radicalmente distintos:**

| | Régimen Local (Pluvial) | Régimen Fluvial (Aguas Arriba) |
|---|---|---|
| **Causa** | Lluvia EN el municipio | Lluvia a 50-100 km, río crece |
| **SAR ¿lo ve?** | ✅ Δ z_VV = -1.6 a -1.85 dB | ❌ Δ z_VV = -0.1 a +0.25 dB |
| **Ejemplos** | Murindó, Vigía, Tarazá | Zaragoza, Caucasia, Turbo |
| **Recall modelo** | Hasta 100% | **0%** |
| **Solución** | LightGBM actual ✅ | Banda L + HAND + grafo |

**Prueba empírica:**
```
MURINDÓ:          z_VV flood = -2.45 | no-flood = -0.86 | Δ = -1.60 dB ✅ EL SAR VE AGUA
ZARAGOZA:         z_VV flood = -0.69 | no-flood = -0.50 | Δ = -0.18 dB ❌ EL SAR NO VE NADA
```

**La ceguera del SAR en Zaragoza NO es un bug del modelo — es una limitación física de Sentinel-1.** La Banda C (~5 cm) no atraviesa el dosel forestal del Bajo Cauca. El agua está ahí, pero el satélite no la ve.

### 3.2 Caracterización Física de las Zonas Vulnerables

Los 8 municipios con 0% recall comparten características físicas que los distinguen del resto de Antioquia:

| Característica | Municipios ciegos | Resto | Ratio |
|---|---|---|---|
| Elevación | 214 m | 687 m | **3.2× más bajos** |
| Pendiente | 556 | 1,333 | **2.4× más planos** |
| Distancia al río | 0.71 km | 3.71 km | **5.2× más cerca** |
| % inundable | 14.4% | 3.4% | **4.3× más** |
| **HAND** | **4 m** | **15 m** | **Al nivel del río** |

**24 municipios** comparten este perfil físico (cluster ribereño). Son todos municipios de río, aguas abajo de grandes cuencas. La física —no la política— define la vulnerabilidad.

### 3.3 La Feature Que el Modelo Usa Pero No Tenemos

`precip_vecinos_3d` (precipitación de municipios cercanos en la misma subregión) fue la **feature #3 del modelo con 5.2% de importancia.** El modelo está DESESPERADO por saber cuánto llueve en los vecinos. La señal existe pero el proxy es ruidoso (usa subregiones políticas, no cuencas reales).

Con un grafo de drenaje correcto (DEM 30m + D8 flow direction), `precip_aguas_arriba_real` podría ser la feature más importante del modelo.

### 3.4 HAND: La Elevación Relativa al Río

Calculado post-entrega. HAND mide cuántos metros está un municipio por encima del río más cercano.

```
ZARAGOZA:  HAND = 4m   ← solo 4 metros sobre el Nechí
CAUCASIA:  HAND = -7m  ← BAJO el nivel del río (¡es una llanura de inundación!)
TURBO:     HAND = 3m   ← a 3 metros sobre el nivel del mar
RIONEGRO:  HAND = 1m   ← sobre la orilla del río Negro
```

`hand_x_precip` es la feature #6 del modelo (3.7% de importancia). HAND + precipitación aguas arriba es la fórmula para resolver el Régimen Fluvial.

### 3.5 El Cluster Físico Supera al Cluster Político

Las 9 subregiones de Antioquia (políticas) aportaron 0.2% de importancia. El cluster físico (elevación < 500m + pendiente < 900 + cerca del río) captura 24 municipios y es usado por el modelo. **La física del terreno —no los mapas de la gobernación— define el riesgo de inundación.**

---

## 4. Features Más Impactantes Descubiertas

### 4.1 Interacciones Precip × Clima (post-entrega)

`precip_acum_3d × QBO50` y `z_VV_mean × precip_acum_3d` son la feature **#1 del modelo mejorado (10.1%).** Las interacciones entre precipitación y fase climática suman 27.6% del peso total.

### 4.2 `sar_x_precip3d` (10.1%)

Cuando llueve Y el SAR muestra agua, la probabilidad de inundación se dispara. Es la interacción más poderosa del modelo.

### 4.3 `precip3d_x_QBO50` (4.3%)

La misma cantidad de lluvia es más peligrosa durante ciertas fases de la oscilación cuasi-bienal. La QBO modula la convección tropical sobre Colombia.

---

## 5. Errores Que No Volveremos a Cometer

| # | Error | Causa | Lección |
|---|-------|-------|---------|
| 1 | 42% nulos en dataset ERA5 | Acentos (Á vs A), columnas duplicadas | Normalizar strings ANTES de cualquier merge |
| 2 | Extender a 1981 no mejoró | ERA5 < CHIRPS | Calidad > cantidad |
| 3 | Reconstruir pipeline existente | No revisar `processed/fase2/` | Auditar datos procesados primero |
| 4 | Targets diferentes sin documentar | `flood_target` vs `target_combinado` | Documentar cada target |
| 5 | LSTM en datos tabulares | 0.47% prevalencia | DL no siempre supera ML |
| 6 | Features incompatibles entre modelos | Columnas `_x`, `_y`, `_missing` | Versionar datasets |
| 7 | Umbral por municipio | Sobreajuste | Mínimo 20+ positivos por grupo |
| 8 | Leer 9,487 TIFFs desde Drive | Latencia FUSE/red | Procesar localmente o con xarray |

---

## 6. Lo Que Queda Para Fase 3

| Prioridad | Tarea | Impacto esperado |
|:---------:|-------|:----------------:|
| 🔥🔥🔥 | Grafo de drenaje con DEM 30m + D8 flow direction | Desbloquea `precip_aguas_arriba` |
| 🔥🔥🔥 | Datos SAR Banda L (ALOS-2/NISAR) para zonas con dosel | Elimina ceguera del SAR en 8 municipios |
| 🔥🔥 | Completar extracción TIFFs (100 puntos × 548 fechas) | Habilita ConvLSTM |
| 🔥🔥 | Fusión IDEAM + CHIRPS (LightGBM regressor) | Mejor precipitación en montaña |
| 🔥 | ConvLSTM con DEM como canal | Aprende topología implícitamente |
| 🔥 | Optuna específico para dataset DHIME | +0.01-0.03 AUROC |
| 🔥 | Modelo separado para zona ribereña (24 municipios) | Recall > 0 en Régimen Fluvial |
| ⚡ | HAND mejorado (DEM 30m en vez de 250m) | HAND más preciso |
| ⚡ | PlanetScope (óptico diario) | Validación visual de inundaciones |
