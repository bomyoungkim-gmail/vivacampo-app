"""
Download and setup pre-trained models for VivaCampo Vision.

Available pre-trained models:
1. PlantVillage - Crop disease detection (38 classes, 54k images)
2. iNaturalist - General plant/animal classification (backbone)
3. ImageNet - General image classification (backbone)

For livestock-specific models, we recommend fine-tuning on Brazilian breeds.
"""

import os
import sys
import json
import hashlib
import zipfile
import tarfile
from pathlib import Path
from urllib.request import urlretrieve
from typing import Dict, List, Optional

import tensorflow as tf
from tensorflow import keras


# Pre-trained model registry
PRETRAINED_MODELS = {
    # Crop disease detection models
    "plantvillage_efficientnet": {
        "description": "Plant disease detection trained on PlantVillage dataset",
        "url": "https://tfhub.dev/google/cropnet/classifier/cassava_disease_V1/2",
        "type": "tfhub",
        "task": "crop_disease",
        "classes": 6,  # Cassava diseases
        "source": "Google CropNet",
    },

    # General backbones from TensorFlow Hub
    "efficientnetv2_s_imagenet": {
        "description": "EfficientNetV2-S pre-trained on ImageNet-21k",
        "url": "https://tfhub.dev/google/imagenet/efficientnet_v2_imagenet21k_s/feature_vector/2",
        "type": "tfhub",
        "task": "backbone",
        "output_dim": 1280,
        "source": "TensorFlow Hub",
    },

    "mobilenetv3_large_imagenet": {
        "description": "MobileNetV3-Large pre-trained on ImageNet",
        "url": "https://tfhub.dev/google/imagenet/mobilenet_v3_large_100_224/feature_vector/5",
        "type": "tfhub",
        "task": "backbone",
        "output_dim": 1280,
        "source": "TensorFlow Hub",
    },

    # Brazilian agricultural datasets info
    "embrapa_soybean_diseases": {
        "description": "Soybean diseases dataset from Embrapa",
        "url": "https://www.kaggle.com/datasets/",  # Placeholder
        "type": "dataset",
        "task": "crop_disease",
        "source": "Embrapa / CNPSO",
        "note": "Requires manual download from Embrapa or partner institutions",
    },
}


# Public datasets for training
PUBLIC_DATASETS = {
    "plantvillage": {
        "name": "PlantVillage Dataset",
        "description": "54,306 images of 14 crop species with 38 disease classes",
        "url": "https://www.kaggle.com/datasets/emmarex/plantdisease",
        "classes": 38,
        "size": "~3GB",
        "license": "CC0 Public Domain",
        "suitable_for": ["crop_disease"],
    },

    "plant_leaves": {
        "name": "Plant Leaves Dataset",
        "description": "4,500+ images of healthy and diseased plant leaves",
        "url": "https://data.mendeley.com/datasets/hb74ynkjcn/1",
        "classes": 22,
        "size": "~1GB",
        "license": "CC BY 4.0",
        "suitable_for": ["crop_disease"],
    },

    "cattle_detection": {
        "name": "Cattle Detection Dataset",
        "description": "Cattle images for detection and counting",
        "url": "https://universe.roboflow.com/search?q=cattle",
        "note": "Multiple datasets available on Roboflow Universe",
        "suitable_for": ["cattle_weight", "cattle_health"],
    },

    "pig_detection": {
        "name": "Pig Detection Dataset",
        "description": "Pig images for detection",
        "url": "https://universe.roboflow.com/search?q=pig",
        "note": "Multiple datasets available on Roboflow Universe",
        "suitable_for": ["swine_weight", "swine_health"],
    },

    "poultry_disease": {
        "name": "Poultry Disease Dataset",
        "description": "Poultry fecal images for disease detection",
        "url": "https://www.kaggle.com/datasets/",
        "note": "Search Kaggle for poultry disease datasets",
        "suitable_for": ["poultry_health"],
    },
}


def download_file(url: str, output_path: Path, desc: str = "") -> bool:
    """Download file with progress."""
    import urllib.request

    def progress_hook(count, block_size, total_size):
        percent = count * block_size * 100 // total_size
        sys.stdout.write(f"\r{desc}: {percent}%")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, output_path, progress_hook)
        print()
        return True
    except Exception as e:
        print(f"\nError downloading: {e}")
        return False


def download_tfhub_model(model_url: str, output_dir: Path) -> keras.Model:
    """Download and cache TensorFlow Hub model."""
    import tensorflow_hub as hub

    print(f"Loading TFHub model: {model_url}")

    # TFHub automatically caches models
    model = hub.KerasLayer(model_url, trainable=True)

    return model


def create_finetunable_model(
    backbone_url: str,
    num_classes: int,
    input_size: tuple = (384, 384, 3),
    dropout_rate: float = 0.3,
) -> keras.Model:
    """Create a model with TFHub backbone ready for fine-tuning."""
    import tensorflow_hub as hub

    inputs = keras.Input(shape=input_size)

    # Preprocessing (EfficientNetV2 expects [0, 255] range)
    x = keras.layers.Rescaling(255.0)(inputs)

    # TFHub backbone
    backbone = hub.KerasLayer(backbone_url, trainable=True)
    features = backbone(x)

    # Classification head
    x = keras.layers.Dropout(dropout_rate)(features)
    x = keras.layers.Dense(512, activation="relu")(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Dropout(dropout_rate)(x)
    outputs = keras.layers.Dense(num_classes, activation="softmax")(x)

    model = keras.Model(inputs, outputs)

    return model


def list_available_models():
    """List all available pre-trained models."""
    print("\n" + "=" * 70)
    print("Available Pre-trained Models")
    print("=" * 70)

    for name, info in PRETRAINED_MODELS.items():
        print(f"\n{name}:")
        print(f"  Description: {info['description']}")
        print(f"  Task: {info['task']}")
        print(f"  Source: {info['source']}")
        if "note" in info:
            print(f"  Note: {info['note']}")


def list_public_datasets():
    """List public datasets for training."""
    print("\n" + "=" * 70)
    print("Public Datasets for Training")
    print("=" * 70)

    for name, info in PUBLIC_DATASETS.items():
        print(f"\n{info['name']}:")
        print(f"  Description: {info['description']}")
        print(f"  URL: {info['url']}")
        print(f"  Suitable for: {', '.join(info['suitable_for'])}")
        if "license" in info:
            print(f"  License: {info['license']}")
        if "note" in info:
            print(f"  Note: {info['note']}")


def setup_crop_disease_model(output_dir: Path, num_classes: int = 38) -> keras.Model:
    """
    Setup crop disease detection model with EfficientNetV2 backbone.

    Recommended: Fine-tune on PlantVillage + Brazilian crop datasets.
    """
    print("\nSetting up Crop Disease Detection Model...")

    model = create_finetunable_model(
        backbone_url="https://tfhub.dev/google/imagenet/efficientnet_v2_imagenet21k_s/feature_vector/2",
        num_classes=num_classes,
        input_size=(384, 384, 3),
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Save model architecture
    model.save(output_dir / "crop_disease_base.keras")

    print(f"Model saved to: {output_dir / 'crop_disease_base.keras'}")
    print(f"  Input: (384, 384, 3)")
    print(f"  Output: {num_classes} classes")
    print(f"  Backbone: EfficientNetV2-S (ImageNet-21k)")

    return model


def setup_livestock_weight_model(
    output_dir: Path,
    animal_type: str = "cattle",
) -> keras.Model:
    """
    Setup livestock weight estimation model.

    Recommended: Fine-tune on Brazilian breed images with weight annotations.
    """
    import tensorflow_hub as hub

    print(f"\nSetting up {animal_type.title()} Weight Estimation Model...")

    input_size = (384, 384, 3)
    inputs = keras.Input(shape=input_size)

    # Preprocessing
    x = keras.layers.Rescaling(255.0)(inputs)

    # Backbone
    backbone = hub.KerasLayer(
        "https://tfhub.dev/google/imagenet/efficientnet_v2_imagenet21k_s/feature_vector/2",
        trainable=True,
    )
    features = backbone(x)

    # Shared layers
    shared = keras.layers.Dropout(0.3)(features)
    shared = keras.layers.Dense(512, activation="relu")(shared)
    shared = keras.layers.BatchNormalization()(shared)

    # Weight regression head
    weight_branch = keras.layers.Dense(256, activation="relu")(shared)
    weight_branch = keras.layers.Dropout(0.3)(weight_branch)
    weight_output = keras.layers.Dense(1, name="weight")(weight_branch)

    # BCS classification head (9 classes: BCS 1-9)
    bcs_branch = keras.layers.Dense(256, activation="relu")(shared)
    bcs_branch = keras.layers.Dropout(0.3)(bcs_branch)
    bcs_output = keras.layers.Dense(9, activation="softmax", name="bcs")(bcs_branch)

    model = keras.Model(inputs, {"weight": weight_output, "bcs": bcs_output})

    output_dir.mkdir(parents=True, exist_ok=True)
    model.save(output_dir / f"{animal_type}_weight_base.keras")

    print(f"Model saved to: {output_dir / f'{animal_type}_weight_base.keras'}")
    print(f"  Input: (384, 384, 3)")
    print(f"  Outputs: weight (regression), BCS (9 classes)")

    return model


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Download and setup pre-trained models")
    parser.add_argument("--list-models", action="store_true",
                        help="List available pre-trained models")
    parser.add_argument("--list-datasets", action="store_true",
                        help="List public datasets for training")
    parser.add_argument("--setup", type=str,
                        choices=["crop_disease", "cattle_weight", "swine_weight",
                                 "poultry_health", "all"],
                        help="Setup base model for fine-tuning")
    parser.add_argument("--output-dir", type=str, default="./pretrained",
                        help="Output directory for models")
    parser.add_argument("--num-classes", type=int, default=38,
                        help="Number of classes for classification models")

    args = parser.parse_args()

    if args.list_models:
        list_available_models()
        return

    if args.list_datasets:
        list_public_datasets()
        return

    output_dir = Path(args.output_dir)

    if args.setup == "crop_disease":
        setup_crop_disease_model(output_dir, args.num_classes)

    elif args.setup == "cattle_weight":
        setup_livestock_weight_model(output_dir, "cattle")

    elif args.setup == "swine_weight":
        setup_livestock_weight_model(output_dir, "swine")

    elif args.setup == "all":
        setup_crop_disease_model(output_dir / "crop_disease", args.num_classes)
        setup_livestock_weight_model(output_dir / "cattle", "cattle")
        setup_livestock_weight_model(output_dir / "swine", "swine")

    else:
        list_available_models()
        print("\n" + "-" * 50)
        list_public_datasets()
        print("\n" + "-" * 50)
        print("\nUse --setup to create base models for fine-tuning")
        print("Example: python download_pretrained.py --setup all --output-dir ./pretrained")


if __name__ == "__main__":
    main()
