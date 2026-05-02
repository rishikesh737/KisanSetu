# KisanSetu AI Models

## 🌿 Crop Disease Detection
**Status:** Trained & Verified  
**Model Architecture:** MobileNetV2 (Transfer Learning)  
**Framework:** PyTorch 2.11.0 (CUDA accelerated)

### Dataset Details
- **Source:** PlantVillage (via Kaggle)
- **Total Images:** 20,638 (Pointed at 15 distinct classes)
- **Classes include:** Potato (Early/Late Blight, Healthy), Pepper (Bacterial Spot, Healthy), etc.

### Training Metrics
- **Hardware:** HP Z2 G9 Workstation (NVIDIA GPU)
- **Epochs:** 3
- **Learning Rate:** 0.001
- **Validation Accuracy:** **94.72%**

### Inference Performance
- **Sample Test:** 97.60% confidence (Tomato Early Blight)
- **Lightweight Factor:** Optimized for eventual deployment to Flutter mobile app and offline use.

---
*Last Updated: May 2, 2026*
