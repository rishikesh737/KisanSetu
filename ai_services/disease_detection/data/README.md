# Rice Disease Dataset

## Download Instructions

1. **Primary Source:** Download from Kaggle:
   - Dataset: [`tedisetiawan/rice-leaf-disease-dataset`](https://www.kaggle.com/datasets/tedisetiawan/rice-leaf-disease-dataset)
   - Alternative: [`nizorogbezuworkeamanuel/rice-leaf-diseases-dataset`](https://www.kaggle.com/datasets/nizorogbezuworkeamanuel/rice-leaf-diseases-dataset)

2. **Organize into class folders:**
   ```
   data/rice/
   ├── Rice_Bacterial_Blight/   # ~800-1200 images
   ├── Rice_Blast/              # ~800-1200 images
   ├── Rice_Brown_Spot/         # ~800-1200 images
   ├── Rice_Tungro/             # ~800-1200 images
   └── Rice_Healthy/            # ~800-1200 images
   ```

3. **Important:** Folder names must match exactly — the training script
   uses `tf.keras.utils.image_dataset_from_directory()` which reads
   class names from folder names in alphabetical order.

## Expected Class Order (Alphabetical)

| Index | Class Name |
|-------|------------|
| 0 | Rice_Bacterial_Blight |
| 1 | Rice_Blast |
| 2 | Rice_Brown_Spot |
| 3 | Rice_Healthy |
| 4 | Rice_Tungro |

> **Note:** TensorFlow sorts class folders alphabetically, so `Rice_Healthy`
> will be index 3 and `Rice_Tungro` will be index 4. The training script
> and labels file account for this ordering.

## Image Requirements
- **Format:** JPG or PNG
- **Minimum resolution:** 224×224 (images will be resized during training)
- **Color:** RGB (no grayscale)
- **Minimum images per class:** 500 (recommended: 800+)
