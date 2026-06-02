"""
entrenar_modelo_ganador.py
==========================
Script reproducible para entrenar el modelo LightGBM de predicción
de inundaciones en Antioquia (Fase 2).

Dataset: dataset_fase2_con_dhime.parquet
Target:  flood_target
Output:  lgbm_dhime_con_indices_noaa.txt

Uso:
    python entrenar_modelo_ganador.py
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import json
import unicodedata
import warnings
from sklearn.metrics import (
    precision_recall_curve, roc_auc_score, average_precision_score,
    f1_score, recall_score, precision_score, confusion_matrix
)
from pathlib import Path

warnings.filterwarnings('ignore')

# ─── CONFIGURACIÓN ─────────────────────────────────────────────
RUTA_PROYECTO = '.'  # Todo en esta misma carpeta                    # Cambiar si es necesario
DATASET       = 'dataset_fase2_con_dhime.parquet'
NOAA_IDX      = 'indices_climaticos_mensuales.parquet'
SUSC          = 'susceptibilidad_nina_municipio.csv'
RIVER         = 'river_density_by_municipio.parquet'
OUT_MODEL     = 'lgbm_dhime_con_indices_noaa.txt'
OUT_METRICS   = 'metricas_finales.json'

TARGET        = 'flood_target'
RANDOM_STATE  = 42

# ─── HIPERPARÁMETROS (Optuna v2) ──────────────────────────────
BEST_PARAMS = {
    'learning_rate': 0.00599596607691301,
    'num_leaves': 251,
    'max_depth': 7,
    'min_child_samples': 46,
    'subsample': 0.3316055307454994,
    'subsample_freq': 1,
    'colsample_bytree': 0.39103605034995553,
    'min_split_gain': 0.11769722980153811,
    'reg_alpha': 0.03029888912211985,
    'reg_lambda': 0.012211451760540486,
    'objective': 'binary',
    'verbose': -1,
    'random_state': RANDOM_STATE,
    'n_jobs': -1,
    'class_weight': 'balanced',
}
N_ESTIMATORS = 2000
EARLY_STOP   = 50


# ─── UTILIDADES ────────────────────────────────────────────────
def strip_accents(s):
    """Quita acentos y normaliza a mayúsculas."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', str(s))
        if unicodedata.category(c) != 'Mn'
    )


# ═══════════════════════════════════════════════════════════════
# 1. CARGAR Y ENRIQUECER DATASET
# ═══════════════════════════════════════════════════════════════
print('[1/5] Cargando dataset DHIME...')
df = pd.read_parquet(DATASET)
df['fecha'] = pd.to_datetime(df['fecha'])
df['municipio'] = df['municipio'].str.upper().apply(strip_accents)

# --- NOAA indices ---
print('[2/5] Agregando índices NOAA...')
noaa = pd.read_parquet(NOAA_IDX)
noaa['anio_mes'] = noaa['YR'].astype(str) + '-' + noaa['MON'].astype(str).str.zfill(2)

df['anio_mes'] = df['fecha'].dt.year.astype(str) + '-' + df['fecha'].dt.month.astype(str).str.zfill(2)
noaa_cols = ['anio_mes', 'SOI', 'QBO30', 'QBO50', 'ZWND200',
             'N12_ANOM', 'N3_ANOM', 'N4_ANOM']
df = df.merge(noaa[noaa_cols], on='anio_mes', how='left')

# --- Susceptibilidad ---
susc = pd.read_csv(SUSC)
susc['municipio'] = susc['municipio'].str.upper().apply(strip_accents)
df = df.merge(susc[['municipio', 'pct_inundable']], on='municipio', how='left')

# --- Densidad de drenaje ---
river = pd.read_parquet(RIVER)
river['municipio'] = river['municipio'].apply(strip_accents)
river_cols = ['municipio', 'river_length_km', 'river_density_km_per_km2', 'river_area_pct']
df = df.merge(river[river_cols], on='municipio', how='left')

# ═══════════════════════════════════════════════════════════════
# 2. SELECCIONAR FEATURES
# ═══════════════════════════════════════════════════════════════
print('[3/5] Seleccionando features...')

# Excluir: targets alternativos, IDs, categóricas, columnas con >15% nulos
all_targets = [c for c in df.columns if 'flood' in c.lower() or 'target' in c.lower()]
exclude = [
    'municipio', 'fecha', 'lat', 'lon', 'fecha_mes', 'anio_mes',
    'uso_suelo_cat', 'mapbiomas_cat', 'YR', 'MON',
]
exclude += [c for c in all_targets if c != TARGET]

FEATURES = []
for c in df.columns:
    if c in exclude:
        continue
    if df[c].dtype not in ('float64', 'int64', 'float32', 'int32'):
        continue
    if df[c].isna().mean() > 0.15:
        continue
    FEATURES.append(c)

print(f'   {len(FEATURES)} features seleccionadas')

# ═══════════════════════════════════════════════════════════════
# 3. SPLIT TEMPORAL + IMPUTACIÓN
# ═══════════════════════════════════════════════════════════════
print('[4/5] Split temporal e imputación...')

train = df[df['fecha'].dt.year <= 2023].copy()
val   = df[df['fecha'].dt.year == 2024].copy()
test  = df[df['fecha'].dt.year >= 2025].copy()

# Imputar nulos con mediana del train
for c in FEATURES:
    if train[c].isna().any():
        median = train[c].median()
        for split_df in [train, val, test]:
            split_df[c] = split_df[c].fillna(median if pd.notna(median) else 0)

print(f'   Train: {len(train):,} ({train[TARGET].sum():,} positivos)')
print(f'   Val:   {len(val):,} ({val[TARGET].sum():,} positivos)')
print(f'   Test:  {len(test):,} ({test[TARGET].sum():,} positivos)')

# ═══════════════════════════════════════════════════════════════
# 4. ENTRENAR
# ═══════════════════════════════════════════════════════════════
print(f'[5/5] Entrenando LightGBM ({N_ESTIMATORS} rounds)...')

dtrain = lgb.Dataset(train[FEATURES], label=train[TARGET])
dval   = lgb.Dataset(val[FEATURES],   label=val[TARGET],   reference=dtrain)

model = lgb.train(
    BEST_PARAMS,
    dtrain,
    num_boost_round=N_ESTIMATORS,
    valid_sets=[dval],
    callbacks=[
        lgb.early_stopping(EARLY_STOP),
        lgb.log_evaluation(100),
    ],
)

print(f'   Mejor iteración: {model.best_iteration}')

# ═══════════════════════════════════════════════════════════════
# 5. EVALUAR Y GUARDAR
# ═══════════════════════════════════════════════════════════════
print(f'\n{"="*55}')
print(f'📊 EVALUACIÓN')
print(f'{"="*55}')

# Umbral óptimo en validación
yp_val = model.predict(val[FEATURES])
prec, rec, thrs = precision_recall_curve(val[TARGET], yp_val)
f1s = 2 * prec[:-1] * rec[:-1] / (prec[:-1] + rec[:-1] + 1e-10)
best_thr = float(thrs[np.argmax(f1s)])
print(f'   Umbral óptimo (val): {best_thr:.4f}')

# Métricas por split
metricas = {}
for name, split_df in [('train', train), ('val', val), ('test', test)]:
    y_true = split_df[TARGET].values
    y_prob = model.predict(split_df[FEATURES])
    y_pred = (y_prob >= best_thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    m = {
        'n': len(y_true),
        'n_pos': int(y_true.sum()),
        'auroc': float(roc_auc_score(y_true, y_prob)),
        'auprc': float(average_precision_score(y_true, y_prob)),
        'f1': float(f1_score(y_true, y_pred, zero_division=0)),
        'recall': float(recall_score(y_true, y_pred, zero_division=0)),
        'precision': float(precision_score(y_true, y_pred, zero_division=0)),
        'tp': int(tp), 'fp': int(fp), 'tn': int(tn), 'fn': int(fn),
        'umbral': best_thr,
    }
    metricas[name] = m
    print(f'   {name:5s}: AUROC={m["auroc"]:.4f}  F1={m["f1"]:.4f}  '
          f'Recall={m["recall"]:.4f}  Prec={m["precision"]:.4f}  '
          f'TP={tp} FP={fp} FN={fn}')

# Guardar modelo
model.save_model(OUT_MODEL)
print(f'\n✅ Modelo guardado: {OUT_MODEL}')

# Guardar métricas
with open(OUT_METRICS, 'w') as f:
    json.dump({
        'modelo': 'LightGBM_DHIME_NOAA',
        'target': TARGET,
        'n_features': len(FEATURES),
        'features': FEATURES,
        'umbral': best_thr,
        'train': metricas['train'],
        'val': metricas['val'],
        'test': metricas['test'],
    }, f, indent=2, default=str)
print(f'✅ Métricas guardadas: {OUT_METRICS}')

# Feature importance
imp = pd.DataFrame({
    'feature': FEATURES,
    'importance': model.feature_importance(importance_type='gain'),
})
imp['pct'] = imp['importance'] / imp['importance'].sum() * 100
imp = imp.sort_values('importance', ascending=False)
print(f'\n🔍 Top 10 features:')
for _, row in imp.head(10).iterrows():
    print(f'   {row["feature"]:30s} {row["pct"]:5.1f}%')
