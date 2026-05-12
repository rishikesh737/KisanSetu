import torch
import torch.nn as nn
from torchvision import models
from dataset import get_data_loaders


def evaluate_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # We only need the validation loader for this
    _, val_loader, classes = get_data_loaders()
    num_classes = len(classes)

    print("🧠 Rebuilding architecture and loading weights...")
    # 1. Rebuild the empty MobileNetV2 architecture with our 15-node head
    model = models.mobilenet_v2()
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)

    # 2. Inject your newly trained weights into the empty architecture
    model.load_state_dict(torch.load("mobilenet_v2_kisansetu.pt", map_location=device))
    model = model.to(device)

    # 3. Lock the model (turns off training-specific behaviors like Dropout)
    model.eval()

    correct = 0
    total = 0

    print("🧪 Testing model against 4,128 unseen validation images...")
    # torch.no_grad() tells PyTorch not to calculate gradients, saving massive memory/time
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)

            # Make the predictions
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)

            # Tally the score
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total
    print(f"\n🎯 Final KisanSetu Model Accuracy: {accuracy:.2f}%")


if __name__ == "__main__":
    evaluate_model()
