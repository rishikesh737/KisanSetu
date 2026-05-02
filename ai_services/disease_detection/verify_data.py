import os
import torchvision.datasets as datasets

# Point this to where the extracted image folders actually live
# Depending on the zip structure, it might be 'research/dataset/PlantVillage'
DATA_DIR = "research/dataset/PlantVillage"


def main():
    try:
        # Load the dataset using PyTorch's ImageFolder
        dataset = datasets.ImageFolder(root=DATA_DIR)

        print("\n✅ AI Environment & Dataset Successfully Linked!")
        print(f"🌿 Total Images Found: {len(dataset)}")
        print(f"📊 Total Disease Classes: {len(dataset.classes)}")
        print("\nFirst 5 Classes:")
        for i, cls in enumerate(dataset.classes[:5]):
            print(f"  - {cls}")

    except FileNotFoundError:
        print(f"\n❌ Error: Could not find images in {DATA_DIR}.")
        print(
            "Run 'ls research/dataset' to see exactly what folder the zip extracted into, and update the DATA_DIR path!"
        )


if __name__ == "__main__":
    main()
