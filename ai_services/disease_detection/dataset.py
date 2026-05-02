import os
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, random_split

DATA_DIR = "research/dataset/PlantVillage"
BATCH_SIZE = 32  # We will feed the model 32 images at a time


def get_data_loaders():
    # 1. Define Transformations (The Prep Station)
    # MobileNetV2 demands exactly 224x224 images and ImageNet color normalization.

    # Train transforms include Data Augmentation (flipping/rotating) to prevent memorization
    train_transforms = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    # Validation transforms just resize and normalize (we don't randomly flip our test data!)
    val_transforms = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    # 2. Load the dataset
    full_dataset = datasets.ImageFolder(root=DATA_DIR, transform=train_transforms)

    # 3. Split into Training (80%) and Validation (20%)
    total_size = len(full_dataset)
    train_size = int(0.8 * total_size)
    val_size = total_size - train_size

    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    # Important: Override the validation dataset's transform so we don't augment it
    val_dataset.dataset.transform = val_transforms

    # 4. Create DataLoaders (These handle shuffling and batching for the CPU/GPU)
    # Using num_workers=2 leverages your HP Workstation's multi-core CPU to load images faster
    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2
    )

    print(
        f"✅ Data Pipeline Ready: {train_size} training images, {val_size} validation images."
    )
    return train_loader, val_loader, full_dataset.classes


if __name__ == "__main__":
    # Quick sanity check to ensure the pipeline is working
    train_loader, val_loader, classes = get_data_loaders()

    # Grab one single batch of data to inspect
    images, labels = next(iter(train_loader))
    print(
        f"📦 Batch shape: {images.shape} -> (Batch_Size, Color_Channels, Height, Width)"
    )
