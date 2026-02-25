# 🌊 Antioquia Flood AI — Fase 2: Modelo LSTM de Predicción de Inundaciones

> **Proyecto académico — Universidad Nacional de Colombia, sede Bogotá**  
> Asignatura: Redes Neuronales  
> Grupo: **Antioquia Flood AI**

---

## 📌 Descripción general

Este repositorio contiene la **Fase 2 (modelo final)** del proyecto de predicción de inundaciones en el departamento de Antioquia, Colombia.

La Fase 1 ([`antioquia-flood-mlp`](https://github.com/Antioquia-Flood-AI/antioquia-flood-mlp)) exploró arquitecturas de redes poco profundas (MLP). Esta fase expande la investigación hacia **Deep Learning** con una red **LSTM (Long Short-Term Memory)**, capaz de capturar dependencias temporales en series de precipitación e integrar variables espaciales derivadas de imágenes satelitales y modelos de elevación digital.

---

## 👥 Equipo

| Rol | Nombre |
|-----|--------|
| Proyecto académico | Universidad Nacional de Colombia, sede Bogotá |
| Asignatura | Redes Neuronales |
| Grupo | Antioquia Flood AI |

---

## 🧠 Arquitectura del modelo

### Red LSTM (Long Short-Term Memory)

| Característica | Detalle |
|---|---|
| **Tipo de red** | LSTM — Deep Neural Network |
| **Tipo de problema** | Clasificación multiclase de profundidad de inundación |
| **Clases objetivo** | `<0.5 m` / `0.5–1.0 m` / `1.0–1.5 m` / `>1.5 m` |

La arquitectura LSTM se eligió por su capacidad estándar para modelar **series temporales hidrológicas**, procesando la secuencia de precipitación horaria como entrada principal y complementándola con *features* espaciales del DEM y la cobertura del suelo.

---

## 📥 Variables de entrada (X)

| Fuente | Variable | Descripción |
|--------|----------|-------------|
| **IDEAM** | Precipitación horaria por estación | Serie temporal secuencial — entrada principal al LSTM |
| **Sentinel-1 (SAR)** | Bandas VV y VH | Imágenes de radar de apertura sintética para el período analizado |
| **DEM SRTM** | Elevación | Modelo digital de elevación del terreno |
| **DEM SRTM** | Pendiente | Gradiente topográfico calculado a partir del DEM |
| **DEM SRTM** | Distancia a ríos | Proximidad a la red hidrográfica |
| **MapBiomas** | Clase de uso del suelo | Categoría de cobertura vegetal o uso humano |
| **MapBiomas** | Impermeabilidad | Porcentaje de superficie impermeable por celda |

---

## 🎯 Variable objetivo (Y)

Categoría de **profundidad de inundación** según los polígonos de períodos de retorno del IDEAM:

| Código | Período de retorno |
|--------|-------------------|
| TR10 | 10 años |
| TR20 | 20 años |
| TR50 | 50 años |
| TR100 | 100 años |

Las clases de profundidad son: **`<0.5 m`**, **`0.5–1.0 m`**, **`1.0–1.5 m`** y **`>1.5 m`**.

---

## ✅ Justificación técnica

El LSTM es la arquitectura estándar para series temporales hidrológicas. Estudios colombianos recientes validaron su eficacia con datos similares:

- **Río Tuluá (2025):** correlación de hasta **0.98** con datos de precipitación y DEM.
- **Boyacá (2024):** resultados equivalentes usando arquitecturas LSTM sobre series horarias del IDEAM.

Estas referencias respaldan la elección del LSTM como modelo final de este proyecto.

---

## 🗂 Estructura del repositorio

```
antioquia-flood-lstm/
├── README.md          # Documentación del proyecto
├── LICENSE            # Licencia del repositorio
└── .gitignore
```

> Los notebooks, scripts de preprocesamiento y el modelo entrenado se añadirán conforme avance el desarrollo.

---

## 🔗 Referencias y recursos

- Fase 1 del proyecto (MLP): [antioquia-flood-mlp](https://github.com/Antioquia-Flood-AI/antioquia-flood-mlp)
- Datos de estaciones: [IDEAM](http://www.ideam.gov.co/)
- Imágenes SAR: [Sentinel-1, Copernicus/ESA](https://sentinel.esa.int/web/sentinel/missions/sentinel-1)
- DEM: [SRTM, NASA](https://www2.jpl.nasa.gov/srtm/)
- Cobertura del suelo: [MapBiomas Colombia](https://colombia.mapbiomas.org/)

---

## 📄 Licencia

Este proyecto se distribuye bajo los términos de la licencia incluida en el archivo [`LICENSE`](./LICENSE).
