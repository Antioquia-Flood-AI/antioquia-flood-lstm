# 🌊 Antioquia Flood LSTM — Predicción de Profundidad de Inundación con Red Neuronal Profunda

> **Fase 2 · Modelo final** — Red LSTM (Long Short-Term Memory) para predicción de profundidad de inundación en municipios de Antioquia, Colombia.  
> Construida sobre la línea base establecida en la [Fase 1 (MLP)](https://github.com/Antioquia-Flood-AI/antioquia-flood-mlp).

---

## ❓ Pregunta de investigación

> **¿Dada la secuencia de precipitación horaria reciente y las condiciones espaciales del terreno, qué profundidad de inundación se espera en las próximas horas?**

---

## 🧠 Arquitectura del modelo

| Componente | Detalle |
|---|---|
| **Tipo** | Deep Neural Network — LSTM (Long Short-Term Memory) |
| **Entrada secuencial** | Series temporales de precipitación horaria por estación IDEAM |
| **Features espaciales** | DEM SRTM (elevación, pendiente, distancia a ríos) + MapBiomas (cobertura del suelo) |
| **Tipo de problema** | Clasificación multiclase de profundidad de inundación |
| **Clases de salida** | `<0.5 m` / `0.5–1.0 m` / `1.0–1.5 m` / `>1.5 m` |
| **Salida** | Softmax (probabilidad por categoría de profundidad) |

---

## 📥 Variables de entrada (features)

| # | Variable | Fuente | Descripción |
|---|---|---|---|
| 1 | Precipitación horaria por estación | IDEAM | Serie temporal secuencial — entrada principal al LSTM |
| 2 | Banda SAR VV | Sentinel-1 | Backscatter en polarización vertical-vertical para el período analizado |
| 3 | Banda SAR VH | Sentinel-1 | Backscatter en polarización vertical-horizontal para el período analizado |
| 4 | Elevación media | DEM SRTM | Elevación del terreno derivada del modelo digital de elevación (30 m) |
| 5 | Pendiente | DEM SRTM | Gradiente topográfico calculado a partir del DEM |
| 6 | Distancia a ríos | DEM SRTM | Proximidad al cauce más cercano derivada de la red hidrográfica |
| 7 | Clase de uso del suelo | MapBiomas | Categoría de cobertura vegetal o uso humano |
| 8 | Impermeabilidad | MapBiomas | Porcentaje de superficie impermeable por celda |

---

## 🎯 Variable objetivo (Y)

| Clase | Profundidad | Período de retorno de referencia |
|---|---|---|
| 1 | `< 0.5 m` | TR10 — período de retorno 10 años |
| 2 | `0.5 – 1.0 m` | TR20 — período de retorno 20 años |
| 3 | `1.0 – 1.5 m` | TR50 — período de retorno 50 años |
| 4 | `> 1.5 m` | TR100 — período de retorno 100 años |

La etiqueta proviene de los **polígonos de inundación TR10/TR20/TR50/TR100 del IDEAM**.

---

## 🗂️ Fuentes de datos

| Fuente | Tipo de datos |
|---|---|
| <a href="http://www.ideam.gov.co/">IDEAM</a> | Series de precipitación horaria por estación + polígonos TR de inundación |
| <a href="https://sentinel.esa.int/web/sentinel/missions/sentinel-1">Sentinel-1 (ESA/Copernicus)</a> | Imágenes SAR (bandas VV y VH) |
| <a href="https://www2.jpl.nasa.gov/srtm/">NASA SRTM DEM</a> | Modelo digital de elevación (resolución 30 m) |
| <a href="https://colombia.mapbiomas.org/">MapBiomas Colombia</a> | Cobertura y uso del suelo (impervious surface) |
| <a href="https://dagran.antioquia.gov.co/">DAGRAN</a> | Reportes históricos de inundaciones en Antioquia |

---

## ✅ Justificación del modelo

El LSTM es la **arquitectura estándar para series temporales hidrológicas**. Su uso permite:

- Capturar **dependencias temporales** en la secuencia de precipitación horaria que un MLP no puede modelar.
- Integrar **features espaciales** del DEM e imágenes SAR como contexto complementario a la serie temporal.
- Predecir no solo si ocurre una inundación, sino **qué tan profunda será**, superando la clasificación binaria de la Fase 1.

Estudios colombianos recientes validan esta elección:
- **Río Tuluá (2025):** correlación de hasta **0.98** con arquitectura LSTM sobre datos similares.
- **Boyacá (2024):** resultados equivalentes usando series horarias del IDEAM con LSTM.

---

## 🗺️ Cobertura geográfica

- **Departamento:** Antioquia, Colombia
- **Unidad de análisis:** Municipio / celda espacial
- **Número de municipios:** 125

---

## 🔁 Flujo de trabajo

```
Datos crudos (IDEAM, Sentinel-1, SRTM, MapBiomas, DAGRAN)
        │
        ▼
Preprocesamiento & feature engineering
(ventanas temporales de precipitación, alineación espacial de rasters)
        │
        ▼
Entrenamiento LSTM (PyTorch / Keras)
        │
        ▼
Evaluación: F1 · AUC-ROC · Recall · Matriz de confusión multiclase
        │
        ▼
Comparación con línea base MLP (Fase 1)
```

---

## 🛠️ Stack tecnológico

- **Lenguaje:** Python 3.10+
- **Entorno de desarrollo:** Google Colab / Kaggle Notebooks
- **Frameworks de ML:** PyTorch o Keras (TensorFlow)
- **Manipulación de datos:** pandas, numpy
- **Datos geoespaciales:** geopandas, rasterio
- **Visualización:** matplotlib, seaborn

---

## 📁 Estructura del proyecto

```
antioquia-flood-lstm/
├── data/
│   ├── raw/            # Datos originales sin procesar
│   └── processed/      # Datos limpios y features generadas
├── notebooks/          # Jupyter / Colab notebooks
├── src/
│   ├── data/           # Scripts de descarga y preprocesamiento
│   ├── features/       # Ingeniería de características
│   └── models/         # Definición y entrenamiento del LSTM
├── models/             # Modelos entrenados (.pt / .h5)
├── reports/            # Métricas, gráficas y resultados
├── requirements.txt
└── README.md
```

---

## 📊 Métricas de evaluación

Dado el desbalance esperado de clases, se priorizan las mismas métricas de referencia usadas en la Fase 1:

- **AUC-ROC** — capacidad discriminativa general (versión multiclase OvR)
- **F1-score (macro)** — balance entre precisión y recall en todas las clases
- **Recall (sensibilidad)** — minimizar falsos negativos en clases de mayor profundidad
- **Matriz de confusión multiclase** — análisis detallado de errores entre categorías

---

## 👥 Equipo

- Proyecto académico — Universidad Nacional de Colombia, sede Bogotá
- Grupo: **Antioquia Flood AI** - Equipo de trabajo de la asignatura Redes Neuronales

---

## 📄 Licencia

Este proyecto está bajo la licencia incluida en el archivo <a href="./LICENSE">LICENSE</a>.
