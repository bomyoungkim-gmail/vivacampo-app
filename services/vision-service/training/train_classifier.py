"""
Training script for classification models (disease detection, health assessment).
"""

import os
import argparse
import json
from pathlib import Path
from datetime import datetime

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks

from dataset import DatasetConfig, ImageClassificationDataset


def create_model(
    num_classes: int,
    input_size: tuple = (384, 384, 3),
    backbone: str = "efficientnetv2-s",
    dropout_rate: float = 0.3,
    freeze_backbone: bool = False,
) -> keras.Model:
    """Create classification model with EfficientNetV2 backbone."""

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

    if freeze_backbone:
        base_model.trainable = False

    # Build model
    inputs = keras.Input(shape=input_size)

    # Preprocessing layer
    x = keras.applications.efficientnet_v2.preprocess_input(inputs)

    # Feature extraction
    features = base_model(x, training=not freeze_backbone)

    # Classification head
    x = layers.Dropout(dropout_rate)(features)
    x = layers.Dense(512, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(dropout_rate)(x)

    outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)

    model = keras.Model(inputs, outputs)

    return model


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

    dataset = ImageClassificationDataset(config)
    train_ds = dataset.get_train_dataset()
    val_ds = dataset.get_val_dataset()

    # Save class mapping
    class_mapping = {
        "class_names": dataset.class_names,
        "class_to_idx": dataset.class_to_idx,
    }
    with open(output_dir / "class_mapping.json", "w") as f:
        json.dump(class_mapping, f, indent=2)

    # Create model
    model = create_model(
        num_classes=len(dataset.class_names),
        input_size=(args.image_size, args.image_size, 3),
        backbone=args.backbone,
        dropout_rate=args.dropout,
        freeze_backbone=args.freeze_backbone,
    )

    # Compile
    optimizer = keras.optimizers.AdamW(
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
    )

    model.compile(
        optimizer=optimizer,
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.summary()

    # Callbacks
    run_name = f"{args.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    training_callbacks = [
        callbacks.ModelCheckpoint(
            filepath=str(output_dir / f"{run_name}_best.keras"),
            save_best_only=True,
            monitor="val_accuracy",
            mode="max",
        ),
        callbacks.EarlyStopping(
            monitor="val_accuracy",
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

    # Class weights for imbalanced data
    class_weights = None
    if args.use_class_weights:
        class_weights = dataset.get_class_weights()
        print(f"Using class weights: {class_weights}")

    # Train
    print(f"\nStarting training: {run_name}")
    print(f"  Classes: {len(dataset.class_names)}")
    print(f"  Backbone: {args.backbone}")
    print(f"  Image size: {args.image_size}x{args.image_size}")

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        callbacks=training_callbacks,
        class_weight=class_weights,
    )

    # Save final model
    model.save(str(output_dir / f"{run_name}_final.keras"))

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
        "num_classes": len(dataset.class_names),
        "train_samples": len(dataset.train_samples),
        "val_samples": len(dataset.val_samples),
        "final_val_accuracy": float(history.history["val_accuracy"][-1]),
        "best_val_accuracy": float(max(history.history["val_accuracy"])),
    }
    with open(output_dir / f"{run_name}_config.json", "w") as f:
        json.dump(training_config, f, indent=2)

    print(f"\nTraining complete!")
    print(f"  Final val accuracy: {history.history['val_accuracy'][-1]:.4f}")
    print(f"  Best val accuracy: {max(history.history['val_accuracy']):.4f}")
    print(f"  Model saved to: {output_dir / f'{run_name}_best.keras'}")

    return model, history


def main():
    parser = argparse.ArgumentParser(description="Train classification model")

    # Data
    parser.add_argument("--data-dir", type=str, required=True,
                        help="Path to dataset directory")
    parser.add_argument("--output-dir", type=str, default="./outputs",
                        help="Output directory for models and logs")
    parser.add_argument("--model-name", type=str, default="classifier",
                        help="Model name for saving")

    # Model
    parser.add_argument("--backbone", type=str, default="efficientnetv2-s",
                        choices=["efficientnetv2-s", "efficientnetv2-m", "mobilenetv3"],
                        help="Backbone architecture")
    parser.add_argument("--image-size", type=int, default=384,
                        help="Input image size")
    parser.add_argument("--dropout", type=float, default=0.3,
                        help="Dropout rate")
    parser.add_argument("--freeze-backbone", action="store_true",
                        help="Freeze backbone weights")

    # Training
    parser.add_argument("--batch-size", type=int, default=32,
                        help="Batch size")
    parser.add_argument("--epochs", type=int, default=100,
                        help="Number of epochs")
    parser.add_argument("--learning-rate", type=float, default=1e-4,
                        help="Learning rate")
    parser.add_argument("--weight-decay", type=float, default=1e-5,
                        help="Weight decay")
    parser.add_argument("--val-split", type=float, default=0.2,
                        help="Validation split ratio")
    parser.add_argument("--early-stopping-patience", type=int, default=15,
                        help="Early stopping patience")
    parser.add_argument("--use-class-weights", action="store_true",
                        help="Use class weights for imbalanced data")
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
