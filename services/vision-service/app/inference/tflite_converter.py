"""
TFLite Converter

Converts Keras models to TensorFlow Lite format with various optimization options.
Optimized for mobile and edge deployment (offline inference).
"""

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import numpy as np
import tensorflow as tf
import structlog

logger = structlog.get_logger()


class TFLiteConverter:
    """
    Utility class for converting Keras models to TFLite format.

    Supports:
    - Dynamic range quantization (default)
    - Full integer quantization (int8)
    - Float16 quantization
    - Edge TPU compilation (Coral)
    """

    def __init__(self, output_dir: str | Path = "models_tflite"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert(
        self,
        model: tf.keras.Model,
        model_name: str,
        quantization: str = "dynamic",
        representative_dataset: Optional[Callable] = None,
        target_ops: Optional[List] = None,
        optimize_for_size: bool = True,
    ) -> Dict[str, Any]:
        """
        Convert Keras model to TFLite format.

        Args:
            model: Keras model to convert
            model_name: Name for the output file
            quantization: Quantization type:
                - "none": No quantization (float32)
                - "dynamic": Dynamic range quantization (default)
                - "float16": Float16 quantization
                - "int8": Full integer quantization (requires representative_dataset)
            representative_dataset: Generator function for int8 calibration
            target_ops: Target operations (for EdgeTPU compatibility)
            optimize_for_size: Apply size optimizations

        Returns:
            Dict with conversion results and file paths
        """
        logger.info(
            "starting_tflite_conversion",
            model_name=model_name,
            quantization=quantization,
        )

        converter = tf.lite.TFLiteConverter.from_keras_model(model)

        # Apply quantization
        if quantization == "dynamic":
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            suffix = "_dynamic"

        elif quantization == "float16":
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.float16]
            suffix = "_fp16"

        elif quantization == "int8":
            if representative_dataset is None:
                raise ValueError(
                    "int8 quantization requires representative_dataset"
                )
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.representative_dataset = representative_dataset
            converter.target_spec.supported_ops = [
                tf.lite.OpsSet.TFLITE_BUILTINS_INT8
            ]
            converter.inference_input_type = tf.uint8
            converter.inference_output_type = tf.uint8
            suffix = "_int8"

        elif quantization == "none":
            suffix = "_fp32"

        else:
            raise ValueError(f"Unknown quantization type: {quantization}")

        # Additional optimizations
        if optimize_for_size:
            converter._experimental_lower_tensor_list_ops = False

        # Set target ops for EdgeTPU if specified
        if target_ops:
            converter.target_spec.supported_ops = target_ops

        # Convert
        try:
            tflite_model = converter.convert()
        except Exception as e:
            logger.error("conversion_failed", error=str(e))
            raise

        # Save model
        output_path = self.output_dir / f"{model_name}{suffix}.tflite"
        with open(output_path, "wb") as f:
            f.write(tflite_model)

        # Calculate sizes
        original_size = self._get_model_size(model)
        tflite_size = len(tflite_model) / (1024 * 1024)
        compression_ratio = original_size / tflite_size if tflite_size > 0 else 0

        # Validate converted model
        validation = self._validate_tflite(output_path)

        result = {
            "success": True,
            "output_path": str(output_path),
            "quantization": quantization,
            "original_size_mb": round(original_size, 2),
            "tflite_size_mb": round(tflite_size, 2),
            "compression_ratio": round(compression_ratio, 1),
            "validation": validation,
        }

        logger.info("conversion_complete", **result)
        return result

    def convert_all_variants(
        self,
        model: tf.keras.Model,
        model_name: str,
        representative_dataset: Optional[Callable] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Convert model to all quantization variants.

        Returns dict with results for each variant.
        """
        results = {}

        # Float32 (no quantization)
        results["fp32"] = self.convert(
            model, model_name, quantization="none"
        )

        # Dynamic range quantization
        results["dynamic"] = self.convert(
            model, model_name, quantization="dynamic"
        )

        # Float16 quantization
        results["fp16"] = self.convert(
            model, model_name, quantization="float16"
        )

        # Int8 quantization (if representative dataset provided)
        if representative_dataset:
            results["int8"] = self.convert(
                model,
                model_name,
                quantization="int8",
                representative_dataset=representative_dataset,
            )

        # Summary
        logger.info(
            "all_variants_converted",
            model_name=model_name,
            variants=list(results.keys()),
        )

        return results

    def _get_model_size(self, model: tf.keras.Model) -> float:
        """Calculate model size in MB."""
        total_bytes = sum(
            w.numpy().nbytes for w in model.trainable_weights
        )
        total_bytes += sum(
            w.numpy().nbytes for w in model.non_trainable_weights
        )
        return total_bytes / (1024 * 1024)

    def _validate_tflite(self, tflite_path: Path) -> Dict[str, Any]:
        """Validate TFLite model by running inference."""
        try:
            interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
            interpreter.allocate_tensors()

            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()

            # Get input shape
            input_shape = input_details[0]["shape"]

            # Create dummy input
            dummy_input = np.random.random(input_shape).astype(
                input_details[0]["dtype"]
            )

            # Run inference
            interpreter.set_tensor(input_details[0]["index"], dummy_input)
            interpreter.invoke()

            # Get output
            output = interpreter.get_tensor(output_details[0]["index"])

            return {
                "valid": True,
                "input_shape": input_shape.tolist(),
                "input_dtype": str(input_details[0]["dtype"]),
                "output_shape": output.shape,
                "output_dtype": str(output_details[0]["dtype"]),
                "num_outputs": len(output_details),
            }

        except Exception as e:
            logger.error("validation_failed", path=str(tflite_path), error=str(e))
            return {"valid": False, "error": str(e)}

    def create_representative_dataset(
        self,
        sample_images: List[np.ndarray],
        input_size: tuple = (224, 224),
        num_samples: int = 100,
    ) -> Callable:
        """
        Create representative dataset generator for int8 quantization.

        Args:
            sample_images: List of sample images (numpy arrays)
            input_size: Expected input size (height, width)
            num_samples: Maximum number of samples to use

        Returns:
            Generator function for TFLite converter
        """
        from PIL import Image

        def resize_image(img: np.ndarray) -> np.ndarray:
            if img.shape[:2] != input_size:
                pil_img = Image.fromarray(img)
                pil_img = pil_img.resize(
                    (input_size[1], input_size[0]),
                    Image.Resampling.LANCZOS
                )
                img = np.array(pil_img)
            return img.astype(np.float32) / 255.0

        def representative_dataset():
            for img in sample_images[:num_samples]:
                processed = resize_image(img)
                yield [np.expand_dims(processed, axis=0)]

        return representative_dataset

    def benchmark_model(
        self,
        tflite_path: str | Path,
        num_runs: int = 100,
        warmup_runs: int = 10,
    ) -> Dict[str, Any]:
        """
        Benchmark TFLite model inference time.

        Returns:
            Dict with timing statistics
        """
        import time

        interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
        interpreter.allocate_tensors()

        input_details = interpreter.get_input_details()
        input_shape = input_details[0]["shape"]

        # Create dummy input
        dummy_input = np.random.random(input_shape).astype(
            input_details[0]["dtype"]
        )

        # Warmup
        for _ in range(warmup_runs):
            interpreter.set_tensor(input_details[0]["index"], dummy_input)
            interpreter.invoke()

        # Benchmark
        times = []
        for _ in range(num_runs):
            start = time.perf_counter()
            interpreter.set_tensor(input_details[0]["index"], dummy_input)
            interpreter.invoke()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        times = np.array(times)

        return {
            "model_path": str(tflite_path),
            "num_runs": num_runs,
            "mean_ms": round(float(np.mean(times)), 2),
            "std_ms": round(float(np.std(times)), 2),
            "min_ms": round(float(np.min(times)), 2),
            "max_ms": round(float(np.max(times)), 2),
            "p50_ms": round(float(np.percentile(times, 50)), 2),
            "p95_ms": round(float(np.percentile(times, 95)), 2),
            "p99_ms": round(float(np.percentile(times, 99)), 2),
        }

    def generate_mobile_package(
        self,
        models: Dict[str, Path],
        output_path: str | Path,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Package multiple TFLite models for mobile distribution.

        Creates a zip file with models and metadata for React Native / Flutter.
        """
        import json
        import zipfile

        output_path = Path(output_path)

        metadata = {
            "version": "1.0.0",
            "created_at": str(np.datetime64("now")),
            "models": {},
        }

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for model_name, model_path in models.items():
                model_path = Path(model_path)
                if model_path.exists():
                    # Add model file
                    zf.write(model_path, f"models/{model_path.name}")

                    # Get model info
                    file_size = model_path.stat().st_size
                    benchmark = self.benchmark_model(model_path, num_runs=10)

                    metadata["models"][model_name] = {
                        "filename": model_path.name,
                        "size_bytes": file_size,
                        "inference_time_ms": benchmark["mean_ms"],
                    }

            # Add metadata
            if include_metadata:
                zf.writestr(
                    "metadata.json",
                    json.dumps(metadata, indent=2)
                )

        logger.info(
            "mobile_package_created",
            output_path=str(output_path),
            num_models=len(models),
            total_size_mb=round(output_path.stat().st_size / (1024 * 1024), 2),
        )

        return {
            "output_path": str(output_path),
            "metadata": metadata,
        }
