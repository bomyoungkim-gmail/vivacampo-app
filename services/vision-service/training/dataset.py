"""
Dataset utilities for training vision models.
Supports loading from local directories and cloud storage (S3).
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator
import tensorflow as tf
import numpy as np
from PIL import Image
import albumentations as A


class DatasetConfig:
    """Configuration for dataset loading."""

    def __init__(
        self,
        data_dir: str,
        image_size: Tuple[int, int] = (384, 384),
        batch_size: int = 32,
        validation_split: float = 0.2,
        augment: bool = True,
        seed: int = 42,
    ):
        self.data_dir = Path(data_dir)
        self.image_size = image_size
        self.batch_size = batch_size
        self.validation_split = validation_split
        self.augment = augment
        self.seed = seed


def get_augmentation_pipeline(image_size: Tuple[int, int]) -> A.Compose:
    """Returns albumentations augmentation pipeline."""
    return A.Compose([
        A.RandomResizedCrop(
            height=image_size[0],
            width=image_size[1],
            scale=(0.8, 1.0),
        ),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.3),
        A.RandomRotate90(p=0.3),
        A.OneOf([
            A.RandomBrightnessContrast(p=1),
            A.RandomGamma(p=1),
            A.HueSaturationValue(p=1),
        ], p=0.5),
        A.OneOf([
            A.GaussNoise(p=1),
            A.GaussianBlur(blur_limit=3, p=1),
            A.MotionBlur(blur_limit=3, p=1),
        ], p=0.3),
        A.CoarseDropout(
            max_holes=8,
            max_height=32,
            max_width=32,
            p=0.3,
        ),
    ])


def get_validation_pipeline(image_size: Tuple[int, int]) -> A.Compose:
    """Returns validation preprocessing pipeline (no augmentation)."""
    return A.Compose([
        A.Resize(height=image_size[0], width=image_size[1]),
    ])


class ImageClassificationDataset:
    """Dataset for image classification tasks (disease detection, health assessment)."""

    def __init__(self, config: DatasetConfig):
        self.config = config
        self.class_names: List[str] = []
        self.class_to_idx: Dict[str, int] = {}
        self.train_samples: List[Tuple[str, int]] = []
        self.val_samples: List[Tuple[str, int]] = []

        self._load_dataset()

    def _load_dataset(self):
        """Load dataset from directory structure: data_dir/class_name/images."""
        if not self.config.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.config.data_dir}")

        # Discover classes from subdirectories
        self.class_names = sorted([
            d.name for d in self.config.data_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ])
        self.class_to_idx = {name: idx for idx, name in enumerate(self.class_names)}

        # Collect all samples
        all_samples = []
        for class_name in self.class_names:
            class_dir = self.config.data_dir / class_name
            for img_path in class_dir.glob("*"):
                if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                    all_samples.append((str(img_path), self.class_to_idx[class_name]))

        # Shuffle and split
        np.random.seed(self.config.seed)
        np.random.shuffle(all_samples)

        split_idx = int(len(all_samples) * (1 - self.config.validation_split))
        self.train_samples = all_samples[:split_idx]
        self.val_samples = all_samples[split_idx:]

        print(f"Dataset loaded: {len(self.class_names)} classes")
        print(f"  Training samples: {len(self.train_samples)}")
        print(f"  Validation samples: {len(self.val_samples)}")

    def _load_and_preprocess(
        self,
        image_path: str,
        label: int,
        augment: bool = False,
    ) -> Tuple[np.ndarray, int]:
        """Load and preprocess a single image."""
        img = Image.open(image_path).convert('RGB')
        img = np.array(img)

        if augment:
            pipeline = get_augmentation_pipeline(self.config.image_size)
        else:
            pipeline = get_validation_pipeline(self.config.image_size)

        transformed = pipeline(image=img)
        img = transformed['image']

        # Normalize to [0, 1]
        img = img.astype(np.float32) / 255.0

        return img, label

    def _generator(
        self,
        samples: List[Tuple[str, int]],
        augment: bool = False,
    ) -> Generator:
        """Generator for tf.data.Dataset."""
        for img_path, label in samples:
            try:
                img, lbl = self._load_and_preprocess(img_path, label, augment)
                yield img, lbl
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
                continue

    def get_train_dataset(self) -> tf.data.Dataset:
        """Returns training dataset with augmentation."""
        dataset = tf.data.Dataset.from_generator(
            lambda: self._generator(self.train_samples, augment=self.config.augment),
            output_signature=(
                tf.TensorSpec(shape=(*self.config.image_size, 3), dtype=tf.float32),
                tf.TensorSpec(shape=(), dtype=tf.int32),
            )
        )

        dataset = dataset.shuffle(1000)
        dataset = dataset.batch(self.config.batch_size)
        dataset = dataset.prefetch(tf.data.AUTOTUNE)

        return dataset

    def get_val_dataset(self) -> tf.data.Dataset:
        """Returns validation dataset without augmentation."""
        dataset = tf.data.Dataset.from_generator(
            lambda: self._generator(self.val_samples, augment=False),
            output_signature=(
                tf.TensorSpec(shape=(*self.config.image_size, 3), dtype=tf.float32),
                tf.TensorSpec(shape=(), dtype=tf.int32),
            )
        )

        dataset = dataset.batch(self.config.batch_size)
        dataset = dataset.prefetch(tf.data.AUTOTUNE)

        return dataset

    def get_class_weights(self) -> Dict[int, float]:
        """Calculate class weights for imbalanced datasets."""
        class_counts = np.zeros(len(self.class_names))
        for _, label in self.train_samples:
            class_counts[label] += 1

        total = len(self.train_samples)
        weights = {}
        for idx in range(len(self.class_names)):
            if class_counts[idx] > 0:
                weights[idx] = total / (len(self.class_names) * class_counts[idx])
            else:
                weights[idx] = 1.0

        return weights


class WeightEstimationDataset:
    """Dataset for weight estimation (regression + BCS classification)."""

    def __init__(
        self,
        config: DatasetConfig,
        annotations_file: str = "annotations.json",
    ):
        self.config = config
        self.annotations_file = config.data_dir / annotations_file
        self.train_samples: List[Dict] = []
        self.val_samples: List[Dict] = []

        self._load_dataset()

    def _load_dataset(self):
        """
        Load dataset from annotations JSON.
        Expected format:
        {
            "samples": [
                {
                    "image": "path/to/image.jpg",
                    "weight_kg": 450.0,
                    "bcs": 5,  # Body Condition Score 1-9
                    "breed": "Nelore",  # optional
                    "age_months": 24  # optional
                }
            ]
        }
        """
        with open(self.annotations_file, 'r') as f:
            data = json.load(f)

        samples = data['samples']

        # Shuffle and split
        np.random.seed(self.config.seed)
        np.random.shuffle(samples)

        split_idx = int(len(samples) * (1 - self.config.validation_split))
        self.train_samples = samples[:split_idx]
        self.val_samples = samples[split_idx:]

        # Calculate weight statistics for normalization
        weights = [s['weight_kg'] for s in samples]
        self.weight_mean = np.mean(weights)
        self.weight_std = np.std(weights)

        print(f"Weight estimation dataset loaded:")
        print(f"  Training samples: {len(self.train_samples)}")
        print(f"  Validation samples: {len(self.val_samples)}")
        print(f"  Weight range: {min(weights):.1f} - {max(weights):.1f} kg")
        print(f"  Weight mean: {self.weight_mean:.1f} kg, std: {self.weight_std:.1f} kg")

    def _load_and_preprocess(
        self,
        sample: Dict,
        augment: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Load and preprocess a single sample."""
        img_path = self.config.data_dir / sample['image']
        img = Image.open(img_path).convert('RGB')
        img = np.array(img)

        if augment:
            pipeline = get_augmentation_pipeline(self.config.image_size)
        else:
            pipeline = get_validation_pipeline(self.config.image_size)

        transformed = pipeline(image=img)
        img = transformed['image']
        img = img.astype(np.float32) / 255.0

        # Normalize weight
        normalized_weight = (sample['weight_kg'] - self.weight_mean) / self.weight_std

        # BCS is 1-9, convert to 0-8 for classification
        bcs = sample.get('bcs', 5) - 1

        # Labels: [normalized_weight, bcs_class]
        labels = np.array([normalized_weight, bcs], dtype=np.float32)

        return img, labels

    def _generator(
        self,
        samples: List[Dict],
        augment: bool = False,
    ) -> Generator:
        """Generator for tf.data.Dataset."""
        for sample in samples:
            try:
                img, labels = self._load_and_preprocess(sample, augment)
                yield img, labels
            except Exception as e:
                print(f"Error loading {sample.get('image')}: {e}")
                continue

    def get_train_dataset(self) -> tf.data.Dataset:
        """Returns training dataset."""
        dataset = tf.data.Dataset.from_generator(
            lambda: self._generator(self.train_samples, augment=self.config.augment),
            output_signature=(
                tf.TensorSpec(shape=(*self.config.image_size, 3), dtype=tf.float32),
                tf.TensorSpec(shape=(2,), dtype=tf.float32),
            )
        )

        dataset = dataset.shuffle(1000)
        dataset = dataset.batch(self.config.batch_size)
        dataset = dataset.prefetch(tf.data.AUTOTUNE)

        return dataset

    def get_val_dataset(self) -> tf.data.Dataset:
        """Returns validation dataset."""
        dataset = tf.data.Dataset.from_generator(
            lambda: self._generator(self.val_samples, augment=False),
            output_signature=(
                tf.TensorSpec(shape=(*self.config.image_size, 3), dtype=tf.float32),
                tf.TensorSpec(shape=(2,), dtype=tf.float32),
            )
        )

        dataset = dataset.batch(self.config.batch_size)
        dataset = dataset.prefetch(tf.data.AUTOTUNE)

        return dataset
