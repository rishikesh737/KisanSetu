# Rice Expert TFLite Model

Place `rice_expert_v1.tflite` in this directory after training.

## How to generate the model:
```bash
cd ai_services/disease_detection
python train_rice_expert.py
cp rice_expert_v1.tflite ../../app/assets/models/
```

The model expects 224x224 RGB input with raw [0, 255] pixel values.
Normalization is baked into the model graph via a Rescaling layer.
