# JARZ-AI Models

Machine learning model development and artifacts for spatio-temporal rental valuation.

## Structure

- `src/` - Model training and evaluation code
  - `get_data.py` - Data collection and preprocessing
  - `train_model.py` - Model training pipeline
- `notebooks/` - Jupyter notebooks for experimentation
- Model artifacts stored externally (use Git LFS for large files)

## Environment Setup

```bash
cp .env.example .env
# Add your API keys and model paths
```

## Model Architecture

The model learns:
- **Temporal dependence**: Past rent trends and growth patterns
- **Spatial dependence**: Nearby areas' rents and demand metrics
- **Quantile predictions**: P10/P50/P90 confidence bands

## Integration

Models are integrated via the model adapter in `backend/app/model_adapter.py`.
