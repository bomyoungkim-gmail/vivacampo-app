"""
Training script for weight estimation models (cattle, swine weight + BCS).
"""

import os
import argparse
import json
from pathlib import Path
from datetime import datetime

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks
import numpy as np

from dataset import DatasetConfig, WeightEstimationDataset


def create_weight_model(
    input_size: tuple = (384, 384, 3),
    backbone: str = "efficientnetv2-s",
    num_bcs_classes: int = 9,
    dropout_rate: float = 0.3,
) -> keras.Model:
    """
    Create multi-task model for weight estimation and BCS classification.

    Outputs:
        - weight: Normalized weight value (regression)
        - bcs: Body Condition Score 1-9 (classification)
    """

    # Select backbone
    if backbone == "efficientnetv2-s":
        base_model = keras.applications.EfficientNetV2S(
            include_top=False,
            weights="imagenet",
            input_shape=input_size,
            pooling="avg",
        )
    elif backbone == "efficientnetv2-m":
        base_model = keras.applications.EfficientNetV2M(
            include_top=False,
            weights="imagenet",
            input_shape=input_size,
            pooling="avg",
        )
    elif backbone == "mobilenetv3":
        base_model = keras.applications.MobileNetV3Large(
            include_top=False,
            weights="imagenet",
            input_shape=input_size,
            pooling="avg",
        )
    else:
        raise ValueError(f"Unknown backbone: {backbone}")

    inputs = keras.Input(shape=input_size)

    # Preprocessing
    x = keras.applications.efficientnet_v2.preprocess_input(inputs)

    # Feature extraction
    features = base_model(x)

    # Shared dense layers
    shared = layers.Dropout(dropout_rate)(features)
    shared = layers.Dense(512, activation="relu")(shared)
    shared = layers.BatchNormalization()(shared)

    # Weight estimation head (regression)
    weight_branch = layers.Dense(256, activation="relu")(shared)
    weight_branch = layers.Dropout(dropout_rate)(weight_branch)
    weight_branch = layers.Dense(64, activation="relu")(weight_branch)
    weight_output = layers.Dense(1, name="weight")(weight_branch)

    # BCS classification head
    bcs_branch = layers.Dense(256, activation="relu")(shared)
    bcs_branch = layers.Dropout(dropout_rate)(bcs_branch)
    bcs_output = layers.Dense(num_bcs_classes, activation="softmax", name="bcs")(bcs_branch)

    model = keras.Model(inputs, {"weight": weight_output, "bcs": bcs_output})

    return model


class WeightLoss(keras.losses.Loss):
    """Custom loss combining weight MSE and BCS cross-entropy."""

    def __init__(self, weight_loss_weight: float = 1.0, bcs_loss_weight: float = 0.5):
        super().__init__()
        self.weight_loss_weight = weight_loss_weight
        self.bcs_loss_weight = bcs_loss_weight
        self.mse = keras.losses.MeanSquaredError()
        self.ce = keras.losses.SparseCategoricalCrossentropy()


def train(args):
    """Main training function."""

    # Setup directories
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Dataset
    config = DatasetConfig(
        data_dir=args.data_dir,
        image_size=(args.image_size, args.image_size),
        batch_size=args.batch_size,
        validation_split=args.val_split,
        augment=True,
        seed=args.seed,
    )

    dataset = WeightEstimationDataset(config, args.annotations_file)
    train_ds = dataset.get_train_dataset()
    val_ds = dataset.get_val_dataset()

    # Custom data generator that splits labels for multi-output model
    def split_labels(images, labels):
        weight = labels[:, 0:1]  # Keep as (batch, 1)
        bcs = tf.cast(labels[:, 1], tf.int32)  # (batch,)
        return images, {"weight": weight, "bcs": bcs}

    train_ds = train_ds.map(split_labels)
    val_ds = val_ds.map(split_labels)

    # Save normalization parameters
    norm_params = {
        "weight_mean": float(dataset.weight_mean),
        "weight_std": float(dataset.weight_std),
    }
    with open(output_dir / "normalization_params.json", "w") as f:
        json.dump(norm_params, f, indent=2)

    # Create model
    model = create_weight_model(
        input_size=(args.image_size, args.image_size, 3),
        backbone=args.backbone,
        num_bcs_classes=9,  # BCS 1-9
        dropout_rate=args.dropout,
    )

    # Compile with separate losses for each output
    optimizer = keras.optimizers.AdamW(
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
    )

    model.compile(
        optimizer=optimizer,
        loss={
            "weight": keras.losses.MeanSquaredError(),
            "bcs": keras.losses.SparseCategoricalCrossentropy(),
        },
        loss_weights={
            "weight": 1.0,
            "bcs": args.bcs_loss_weight,
        },
        metrics={
            "weight": ["mae"],
            "bcs": ["accuracy"],
        },
    )

    model.summary()

    # Callbacks
    run_name = f"{args.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    training_callbacks = [
        callbacks.ModelCheckpoint(
            filepath=str(output_dir / f"{run_name}_best.keras"),
            save_best_only=True,
            monitor="val_weight_mae",
            mode="min",
        ),
        callbacks.EarlyStopping(
            monitor="val_loss",
            patience=args.early_stopping_patience,
            restore_best_weights=True,
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            min_lr=1e-7,
        ),
        callbacks.TensorBoard(
            log_dir=str(output_dir / "logs" / run_name),
        ),
        callbacks.CSVLogger(
            str(output_dir / f"{run_name}_history.csv"),
        ),
    ]

    # Train
    print(f"\nStarting training: {run_name}")
    print(f"  Backbone: {args.backbone}")
    print(f"  Image size: {args.image_size}x{args.image_size}")
    print(f"  Weight normalization: mean={dataset.weight_mean:.1f}, std={dataset.weight_std:.1f}")

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        callbacks=training_callbacks,
    )

    # Save final model
    model.save(str(output_dir / f"{run_name}_final.keras"))

    # Calculate actual weight MAE (denormalized)
    val_weight_mae = min(history.history["val_weight_mae"])
    actual_mae_kg = val_weight_mae * dataset.weight_std

    # Save training config
    training_config = {
        "model_name": args.model_name,
        "run_name": run_name,
        "backbone": args.backbone,
        "image_size": args.image_size,
        "batch_size": args.batch_size,
        "epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "dropout": args.dropout,
        "train_samples": len(dataset.train_samples),
        "val_samples": len(dataset.val_samples),
        "weight_mean": dataset.weight_mean,
        "weight_std": dataset.weight_std,
        "final_val_weight_mae": float(history.history["val_weight_mae"][-1]),
        "best_val_weight_mae": float(val_weight_mae),
        "best_val_weight_mae_kg": float(actual_mae_kg),
        "final_val_bcs_accuracy": float(history.history["val_bcs_accuracy"][-1]),
    }
    with open(output_dir / f"{run_name}_config.json", "w") as f:
        json.dump(training_config, f, indent=2)

    print(f"\nTraining complete!")
    print(f"  Best val weight MAE: {val_weight_mae:.4f} (normalized)")
    print(f"  Best val weight MAE: {actual_mae_kg:.1f} kg (actual)")
    print(f"  Final val BCS accuracy: {history.history['val_bcs_accuracy'][-1]:.4f}")
    print(f"  Model saved to: {output_dir / f'{run_name}_best.keras'}")

    return model, history


def main():
    parser = argparse.ArgumentParser(description="Train weight estimation model")

    # Data
    parser.add_argument("--data-dir", type=str, required=True,
                        help="Path to dataset directory")
    parser.add_argument("--annotations-file", type=str, default="annotations.json",
                        help="Name of annotations JSON file")
    parser.add_argument("--output-dir", type=str, default="./outputs",
                        help="Output directory for models and logs")
    parser.add_argument("--model-name", type=str, default="weight_estimator",
                        help="Model name for saving")

    # Model
    parser.add_argument("--backbone", type=str, default="efficientnetv2-s",
                        choices=["efficientnetv2-s", "efficientnetv2-m", "mobilenetv3"],
                        help="Backbone architecture")
    parser.add_argument("--image-size", type=int, default=384,
                        help="Input image size")
    parser.add_argument("--dropout", type=float, default=0.3,
                        help="Dropout rate")

    # Training
    parser.add_argument("--batch-size", type=int, default=32,
                        help="Batch size")
    parser.add_argument("--epochs", type=int, default=100,
                        help="Number of epochs")
    parser.add_argument("--learning-rate", type=float, default=1e-4,
                        help="Learning rate")
    parser.add_argument("--weight-decay", type=float, default=1e-5,
                        help="Weight decay")
    parser.add_argument("--bcs-loss-weight", type=float, default=0.5,
                        help="Weight for BCS classification loss")
    parser.add_argument("--val-split", type=float, default=0.2,
                        help="Validation split ratio")
    parser.add_argument("--early-stopping-patience", type=int, default=15,
                        help="Early stopping patience")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")

    args = parser.parse_args()

    # GPU setup
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        print(f"Found {len(gpus)} GPU(s)")
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    else:
        print("No GPU found, using CPU")

    train(args)


if __name__ == "__main__":
    main()
