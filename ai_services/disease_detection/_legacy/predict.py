import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os
import random

# Configuration
MODEL_PATH = "mobilenet_v2_kisansetu.pt"
DATA_DIR = "research/dataset/PlantVillage"


def predict():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 1. Get the class names (alphabetical order as PyTorch loads them)
    classes = sorted(os.listdir(DATA_DIR))

    # 2. Pick a random image from a random folder for testing
    random_class = random.choice(classes)
    class_path = os.path.join(DATA_DIR, random_class)
    random_image_name = random.choice(os.listdir(class_path))
    image_path = os.path.join(class_path, random_image_name)

    print(f"📸 Testing Image: {image_path}")
    print(f"🏷️  Actual Label: {random_class}")

    # 3. Load and Pre-process the image
    image_transforms = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    image = Image.open(image_path).convert("RGB")
    image_tensor = (
        image_transforms(image).unsqueeze(0).to(device)
    )  # Add batch dimension

    # 4. Load the Model
    model = models.mobilenet_v2()
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(classes))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model = model.to(device)
    model.eval()

    # 5. Run Inference
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
        confidence, predicted_idx = torch.max(probabilities, 0)

    predicted_class = classes[predicted_idx]

    print("-" * 30)
    print(f"🤖 AI PREDICTION: {predicted_class}")
    print(f"📊 CONFIDENCE: {confidence.item() * 100:.2f}%")
    print("-" * 30)

    if predicted_class == random_class:
        print("✅ SUCCESS: The model was correct!")
    else:
        print("❌ MISMATCH: The model got this one wrong.")


if __name__ == "__main__":
    predict()
