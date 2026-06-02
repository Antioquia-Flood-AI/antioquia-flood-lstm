# 📊 Datos y Fuentes — Fase 2 Inundaciones Antioquia

**Fecha:** 2 de junio de 2026  
**Dataset principal:** `processed/fase2/dataset_fase2_con_dhime.parquet`  
**Filas:** 408,443 | **Municipios:** 123 | **Rango:** 2018-01-01 → 2026-05-29

---

## 1. Fuentes de Datos

### 1.1 Precipitación — CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data)

| Campo | Valor |
|-------|-------|
| **Fuente** | UCSB/CHG via Google Earth Engine |
| **Resolución** | ~5 km, diaria |
| **Cobertura** | 2018–2026, 123 municipios |
| **Procesamiento** | Extracción por punto (coordenadas del centroide municipal) |
| **Features generadas** | `chirps_precip_mm_dia`, `precip_acum_1d/3d/7d/15d/30d`, `p90_precip_3d` |
| **Archivo raw** | `raw/CHIRPS p05 tiff/` (TIFFs diarios, ~44 MB) |
| **Archivo procesado** | `processed/fase1/chirps_municipio/chirps_municipio_diario_YYYY.parquet` |

### 1.2 Radar Satelital — SAR Sentinel-1

| Campo | Valor |
|-------|-------|
| **Fuente** | ESA Sentinel-1, banda C, descendente |
| **Resolución** | 10m, cada 6 días |
| **Cobertura** | 2018–2026, 123 municipios |
| **Procesamiento** | Google Earth Engine: filtro Speckle, extracción por punto |
| **Features generadas** | `VV_mean`, `VH_mean`, `VV_minus_VH`, `z_VV_mean`, `n_scenes` |
| **Archivo raw** | `raw/SAR Sentinel-1 — Google Earth Engine/` (~43 GB) |
| **Nota** | Los datos raw son compuestas anuales. Las features en el dataset DHIME vienen de extracciones puntuales ya procesadas. |

### 1.3 Índices Climáticos — NOAA

| Campo | Valor |
|-------|-------|
| **Fuente** | NOAA Climate Prediction Center |
| **Cobertura** | 1950–presente, mensual |
| **Índices utilizados** | ONI (Oceanic Niño Index), SOI, QBO30, QBO50, ZWND200, N12/N3/N4 ANOM |
| **Archivo raw** | `raw/indices_noaa/` (34 archivos, ASCII + parquet) |
| **Archivo procesado** | `raw/indices_noaa/indices_climaticos_mensuales.parquet` (22 columnas, 2018–2025) |
| **Procesamiento** | Merge por año-mes al dataset principal |

### 1.4 Variables Atmosféricas — Open-Meteo

| Campo | Valor |
|-------|-------|
| **Fuente** | Open-Meteo API (ERA5-Land) |
| **Cobertura** | 2018–2026, 123 municipios |
| **Variables** | temperatura_media, temperatura_max, humedad_media, viento_medio |
| **Archivo procesado** | `processed/fase2/openmeteo_municipio_diario_2018_2026.parquet` |

### 1.5 Topografía — AW3D30 (JAXA)

| Campo | Valor |
|-------|-------|
| **Fuente** | JAXA ALOS World 3D |
| **Resolución** | 30m |
| **Cobertura** | Todo Antioquia |
| **Features generadas** | `elevacion_msnm`, `pendiente_val`, `slope_mean/max/p90`, `twi_mean/max/p90/p99`, `acc_mean/max/p90/p99` |
| **Archivo raw** | `raw/Topografía y cartografía IGAC/output_AW3D30.tif` (190 MB) |

### 1.6 Amenaza de Inundación — TR (Tiempo de Retorno)

| Campo | Valor |
|-------|-------|
| **Fuente** | Modelaciones hidráulicas IGAC/IDEAM |
| **Cobertura** | 35 centros poblados |
| **Features generadas** | `tr_score_mean_all`, `tr_amenaza100_score_mean`, `tr_prof10/20/50/100_score_mean`, `tr_high_share_all` |
| **Archivo raw** | `raw/TR centros poblados varios/` (GeoJSON, ~1.8 GB) |

### 1.7 Susceptibilidad de Inundación

| Campo | Valor |
|-------|-------|
| **Fuente** | Procesamiento de áreas inundables en eventos Niña |
| **Features** | `pct_inundable`, `area_inundable_km2` |
| **Archivo** | `processed/fase2/susceptibilidad_nina_municipio.csv` (125 municipios) |

### 1.8 Red de Drenaje

| Campo | Valor |
|-------|-------|
| **Fuente** | Carto100000 Colombia (IGAC) |
| **Features** | `distancia_rio_km_real`, `river_length_km`, `river_density_km_per_km2`, `river_area_pct` |
| **Archivos raw** | `raw/mapa vectorial colombia geopackage/antioquia_drenaje_sencillo.geojson`, `antioquia_drenaje_doble.geojson` |
| **Procesamiento** | Buffer 10km alrededor de cada municipio, intersección espacial con líneas y polígonos de drenaje. `river_density_by_municipio.parquet` |

### 1.9 Ground Truth — DAGRAN + UNGRD

| Campo | Valor |
|-------|-------|
| **Fuente** | DAGRAN (Departamento Administrativo de Gestión del Riesgo de Antioquia) + UNGRD |
| **Cobertura** | 1998–2025, 229 municipios (nacional) |
| **Target final** | `flood_target` (1,926 eventos, prevalencia 0.47%) |
| **Target alternativo** | `target_combinado` (5,164 eventos, prevalencia 0.26%) — más eventos pero más ruidoso |
| **Targets auxiliares** | `flood_event` (949), `flood_proxy_sar` (981) |
| **Archivos** | `raw/NUEVO GROUND TRUTH/Ficha de Reporte_Emergencias_2012_Final.xlsx`, `raw/Ground truth inundaciones/eventos_hidricos_reales_antioquia.geojson` |
| **Archivo procesado** | `processed/fase2/target_combinado_dagran_ungrd.csv` |

### 1.10 Niveles de Río — DHIME (IDEAM)

| Campo | Valor |
|-------|-------|
| **Fuente** | IDEAM — Red DHIME |
| **Cobertura** | 2018–2026, 37 estaciones en 31 municipios |
| **Features** | `nivel_med_mean`, `nivel_max_mean` (90-95% nulos — solo donde hay estación) |
| **Archivo raw** | `raw/DHIME IDEAM nivel/` |
| **Archivo adicional** | `raw/Nuevo niveles de rio antioquia/Nivel_Mínimo_del_Rio_20260531_clean.csv` (849K filas, nivel horario) |

---

## 2. Pipeline de Procesamiento

```
┌─────────────────────────────────────────────────────────────────────┐
│                          RAW DATA (~45 GB)                          │
│  CHIRPS │ SAR │ NOAA │ Open-Meteo │ Topografía │ TR │ Drenaje │ GT │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│               PROCESAMIENTO (Google Earth Engine + Python)          │
│  • Extracción por punto (coordenadas municipales)                   │
│  • Acumulados de precipitación (3d, 7d, 15d, 30d)                  │
│  • Merge de índices NOAA por año-mes                                │
│  • Intersección espacial drenaje-municipio (buffer 10km)            │
│  • Imputación de nulos con mediana por municipio                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│        dataset_fase2_con_dhime.parquet (408,443 filas, 63 cols)     │
│        + índices NOAA + pct_inundable + river_density               │
│                    → 52 features finales                            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  SPLIT TEMPORAL: Train ≤2023 | Val = 2024 | Test ≥ 2025            │
│  MODELO: LightGBM (Optuna 250 trials)                               │
│  TARGET: flood_target (1,926 positivos)                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Calidad de Datos

### Nulos por feature
- 0%: estáticas (distancia_rio, elevacion, pendiente, TR, slope, twi, acc)
- 2-3%: CHIRPS, temperatura, humedad, viento
- 4%: ONI
- 7%: SAR (VV, VH)
- 90-95%: DHIME (solo 31 municipios con estaciones) — **excluidas del modelo final**
- 89%: delta_creciente, tendencia_base — **excluidas**

### Estrategia de imputación
- Features meteorológicas: mediana por municipio
- Features estáticas: mediana global de Antioquia
- SAR: mediana por municipio (6.9% de tiles sin datos SAR por cobertura satelital parcial)

### Verificación de fugas temporales
- Split puramente cronológico (sin shuffle)
- Sin features que miren al futuro (todos los acumulados usan ventanas hacia atrás)
- ONI se mergea por año-mes (el valor del mes actual no es fuga porque se conoce al inicio del mes)

---

## 4. Dataset Histórico ERA5 (Exploratorio)

Se construyó un dataset extendido 1981-2025 usando ERA5-Land (Open-Meteo) para intentar usar más ground truth histórico (1998-2017):

| Dataset | Período | Filas | Features | Precip fuente | Target |
|---------|---------|------:|----------|---------------|--------|
| Principal (DHIME) | 2018–2026 | 408K | 63 | CHIRPS | flood_target |
| Histórico (ERA5) | 1981–2025 | 2.02M | 36 | ERA5-Land | target_combinado |

**Resultado:** El dataset ERA5 no mejoró el modelo (AUROC 0.717 vs 0.946 del principal). La diferencia de calidad entre CHIRPS (~5km, calibrado con estaciones) y ERA5-Land (~9km, solo modelo) es significativa para predicción de inundaciones. Además, `target_combinado` resultó ser más ruidoso que `flood_target`.

---

## 5. Tamaños de Archivos

| Archivo | Tamaño | Descripción |
|---------|:------:|-------------|
| `dataset_fase2_con_dhime.parquet` | 83 MB | Dataset principal |
| `dataset_1981_2025_consistente.parquet` | 60 MB | Dataset histórico ERA5 |
| `indices_climaticos_mensuales.parquet` | 21 KB | Índices NOAA mensuales |
| `susceptibilidad_nina_municipio.csv` | 3 KB | Susceptibilidad por municipio |
| `river_density_by_municipio.parquet` | 8 KB | Densidad de drenaje |
| `Nivel_Mínimo_del_Rio_20260531_clean.csv` | 66 MB | Niveles de río (horario) |
