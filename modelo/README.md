# Modelo Ganador

**Cargar con:**
```python
import lightgbm as lgb
model = lgb.Booster(model_file='lgbm_dhime_con_indices_noaa.txt')
```

**Métricas:** AUROC 0.946 | F1 0.593 | Recall 0.561  
**Ver:** `../docs/INFORME_MODELO.md`
