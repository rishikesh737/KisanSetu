import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from dataset import get_data_loaders

# Hyperparameters
EPOCHS = 3
LEARNING_RATE = 0.001


def train_model():
    # 1. Hardware Check: Use the GPU if available, otherwise fallback to the i9 CPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 Initializing on device: {device}")

    # 2. Spin up the data pipeline
    train_loader, val_loader, classes = get_data_loaders()
    num_classes = len(classes)

    # 3. Load the "Master Chef" (MobileNetV2 pre-trained on ImageNet)
    print("🧠 Downloading pre-trained MobileNetV2...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)

    # 4. FREEZE THE CORE: Stop the optimizer from changing the core vision layers
    for param in model.parameters():
        param.requires_grad = False

    # 5. SWAP THE HEAD: Replace the 1000-class output with our 15-class output
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)

    # Move the model to the CPU/GPU
    model = model.to(device)

    # 6. Setup Optimizer and Loss
    # Notice we ONLY give the optimizer the parameters of the NEW classifier head
    optimizer = optim.Adam(model.classifier.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss()

    # 7. The Training Loop
    print(f"🔥 Starting Training Loop for {EPOCHS} Epochs...")
    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0

        for i, (images, labels) in enumerate(train_loader):
            # Move images/labels to the correct hardware
            images, labels = images.to(device), labels.to(device)

            # Clear the old gradients
            optimizer.zero_grad()

            # Forward pass: Make a prediction
            outputs = model(images)
            loss = criterion(outputs, labels)

            # Backward pass: Calculate the errors and update the 15-node head
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

            # Print progress every 100 batches
            if (i + 1) % 100 == 0:
                print(
                    f"  -> Epoch [{epoch+1}/{EPOCHS}], Step [{i+1}/{len(train_loader)}], Loss: {loss.item():.4f}"
                )

        print(
            f"✅ Epoch {epoch+1} completed! Average Loss: {running_loss/len(train_loader):.4f}\n"
        )

    # 8. Save the newly trained model weights
    torch.save(model.state_dict(), "mobilenet_v2_kisansetu.pt")
    print("💾 Training complete! Model weights saved to 'mobilenet_v2_kisansetu.pt'")


if __name__ == "__main__":
    train_model()
