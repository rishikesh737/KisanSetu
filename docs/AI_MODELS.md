# KisanSetu AI Models

## 🌿 Rice Disease Detection (v1 — Offline)
**Status:** Pipeline Ready (awaiting dataset)
**Model Architecture:** MobileNetV2 (Transfer Learning, Fine-tuned)
**Framework:** TensorFlow / Keras → TFLite export
**Inference:** 100% on-device via `tflite_flutter` (no network required)

### Model Specifications
- **Input:** 224×224 RGB image, raw `[0, 255]` pixel values
- **Normalization:** Baked into the model graph via `Rescaling(1/255)` layer
- **Output:** 5-element softmax probability vector
- **Quantization:** Float16 (reduces model size ~2x with negligible accuracy loss)
- **Expected Size:** ~2-4 MB (`.tflite`)

### Target Classes (Alphabetical Order)
| Index | Class | Common Trigger |
|-------|-------|---------------|
| 0 | Rice_Bacterial_Blight | Heavy rainfall / monsoon |
| 1 | Rice_Blast | High humidity (>85%) |
| 2 | Rice_Brown_Spot | Dry conditions |
| 3 | Rice_Healthy | — |
| 4 | Rice_Tungro | Leafhopper vectors |

### Dataset
- **Source:** Kaggle `rice-leaf-disease-dataset` + field photos from Goa/Maharashtra
- **Split:** 80% training / 20% validation (seed=42)
- **Augmentation:** Random flip, rotation (15°), zoom (10%), contrast (10%)

### Training Strategy
1. **Phase A:** Train classifier head only (backbone frozen, 20 epochs, LR=1e-4)
2. **Phase B:** Fine-tune top backbone layers (layers 100+, 10 epochs, LR=1e-5)
3. **Early Stopping:** Monitor `val_accuracy`, patience=5, restore best weights

### Weather Fusion (Environmental Prior)
After TFLite outputs raw probabilities, the Flutter app applies weather-based multipliers:
- **Rice Blast × 1.3** when humidity > 85%
- **Bacterial Blight × 1.3** when rainfall > 50mm
- **Brown Spot × 1.4** when humidity < 65% AND rainfall < 10mm

Probabilities are re-normalized to sum to 1.0 after adjustment.

### Guardrail
- **Confidence threshold:** 85%
- Predictions below 85% show "Scan Unclear" warning
- Effectively rejects out-of-distribution inputs (non-rice leaves)

---

### Legacy Model (Deprecated)
The previous 38-class PlantVillage model (`kisansetu_v38.onnx`) has been archived to `ai_services/disease_detection/_legacy/`. It is retained for reference only.

---
*Last Updated: May 12, 2026*
