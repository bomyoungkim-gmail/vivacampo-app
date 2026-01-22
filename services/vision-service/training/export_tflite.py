"""
Export trained Keras models to TFLite format for mobile deployment.
"""

import os
import argparse
import json
from pathlib import Path
from typing import Optional

import tensorflow as tf
import numpy as np


def representative_dataset_generator(
    data_dir: str,
    num_samples: int = 100,
    image_size: tuple = (384, 384),
):
    """Generator for representative dataset used in INT8 quantization."""
    from PIL import Image

    data_path = Path(data_dir)
    image_files = list(data_path.rglob("*.jpg")) + list(data_path.rglob("*.png"))

    if len(image_files) == 0:
        print(f"Warning: No images found in {data_dir}, using random data")
        for _ in range(num_samples):
            yield [np.random.rand(1, *image_size, 3).astype(np.float32)]
        return

    np.random.shuffle(image_files)

    for img_path in image_files[:num_samples]:
        try:
            img = Image.open(img_path).convert("RGB")
            img = img.resize(image_size)
            img = np.array(img, dtype=np.float32) / 255.0
            img = np.expand_dims(img, 0)
            yield [img]
        except Exception as e:
            print(f"Error loading {img_path}: {e}")
            continue


def convert_to_tflite(
    model_path: str,
    output_path: str,
    quantization: str = "none",
    representative_data_dir: Optional[str] = None,
    image_size: tuple = (384, 384),
) -> dict:
    """
    Convert Keras model to TFLite format.

    Args:
        model_path: Path to .keras model file
        output_path: Output path for .tflite file
        quantization: Quantization type: 'none', 'dynamic', 'float16', 'int8'
        representative_data_dir: Directory with representative images (for INT8)
        image_size: Input image size

    Returns:
        dict with conversion info (size, quantization type)
    """
    print(f"\nConverting: {model_path}")
    print(f"Quantization: {quantization}")

    # Load model
    model = tf.keras.models.load_model(model_path)

    # Create converter
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # Configure quantization
    if quantization == "dynamic":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]

    elif quantization == "float16":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]

    elif quantization == "int8":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.uint8
        converter.inference_output_type = tf.float32

        if representative_data_dir:
            def rep_dataset():
                return representative_dataset_generator(
                    representative_data_dir,
                    num_samples=100,
                    image_size=image_size,
                )
            converter.representative_dataset = rep_dataset
        else:
            print("Warning: No representative data provided for INT8 quantization")
            def rep_dataset():
                for _ in range(100):
                    yield [np.random.rand(1, *image_size, 3).astype(np.float32)]
            converter.representative_dataset = rep_dataset

    # Convert
    tflite_model = converter.convert()

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(tflite_model)

    # Get sizes
    original_size = os.path.getsize(model_path)
    tflite_size = os.path.getsize(output_path)

    info = {
        "model_path": str(model_path),
        "tflite_path": str(output_path),
        "quantization": quantization,
        "original_size_mb": original_size / (1024 * 1024),
        "tflite_size_mb": tflite_size / (1024 * 1024),
        "compression_ratio": original_size / tflite_size,
    }

    print(f"  Original size: {info['original_size_mb']:.2f} MB")
    print(f"  TFLite size: {info['tflite_size_mb']:.2f} MB")
    print(f"  Compression ratio: {info['compression_ratio']:.2f}x")
    print(f"  Saved to: {output_path}")

    return info


def convert_all_variants(
    model_path: str,
    output_dir: str,
    representative_data_dir: Optional[str] = None,
    image_size: tuple = (384, 384),
) -> dict:
    """Convert model to all quantization variants."""

    output_dir = Path(output_dir)
    model_name = Path(model_path).stem

    results = {}

    # No quantization (baseline)
    results["none"] = convert_to_tflite(
        model_path,
        output_dir / f"{model_name}.tflite",
        quantization="none",
        image_size=image_size,
    )

    # Dynamic quantization
    results["dynamic"] = convert_to_tflite(
        model_path,
        output_dir / f"{model_name}_dynamic.tflite",
        quantization="dynamic",
        image_size=image_size,
    )

    # Float16 quantization
    results["float16"] = convert_to_tflite(
        model_path,
        output_dir / f"{model_name}_float16.tflite",
        quantization="float16",
        image_size=image_size,
    )

    # INT8 quantization
    results["int8"] = convert_to_tflite(
        model_path,
        output_dir / f"{model_name}_int8.tflite",
        quantization="int8",
        representative_data_dir=representative_data_dir,
        image_size=image_size,
    )

    # Save conversion report
    with open(output_dir / f"{model_name}_conversion_report.json", "w") as f:
        json.dump(results, f, indent=2)

    return results


def benchmark_tflite(tflite_path: str, num_runs: int = 50) -> dict:
    """Benchmark TFLite model inference time."""
    import time

    # Load model
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Prepare input
    input_shape = input_details[0]["shape"]
    input_dtype = input_details[0]["dtype"]

    if input_dtype == np.uint8:
        input_data = np.random.randint(0, 256, input_shape).astype(np.uint8)
    else:
        input_data = np.random.rand(*input_shape).astype(np.float32)

    # Warmup
    for _ in range(10):
        interpreter.set_tensor(input_details[0]["index"], input_data)
        interpreter.invoke()

    # Benchmark
    times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        interpreter.set_tensor(input_details[0]["index"], input_data)
        interpreter.invoke()
        times.append(time.perf_counter() - start)

    results = {
        "model": tflite_path,
        "num_runs": num_runs,
        "mean_ms": np.mean(times) * 1000,
        "std_ms": np.std(times) * 1000,
        "min_ms": np.min(times) * 1000,
        "max_ms": np.max(times) * 1000,
        "fps": 1.0 / np.mean(times),
    }

    print(f"\nBenchmark: {tflite_path}")
    print(f"  Mean: {results['mean_ms']:.2f} ms")
    print(f"  Std: {results['std_ms']:.2f} ms")
    print(f"  FPS: {results['fps']:.1f}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Export Keras model to TFLite")

    parser.add_argument("model_path", type=str,
                        help="Path to Keras model (.keras file)")
    parser.add_argument("--output-dir", type=str, default="./tflite",
                        help="Output directory for TFLite models")
    parser.add_argument("--quantization", type=str, default="all",
                        choices=["none", "dynamic", "float16", "int8", "all"],
                        help="Quantization type (or 'all' for all variants)")
    parser.add_argument("--representative-data", type=str, default=None,
                        help="Directory with representative images for INT8 quantization")
    parser.add_argument("--image-size", type=int, default=384,
                        help="Input image size")
    parser.add_argument("--benchmark", action="store_true",
                        help="Run benchmark after conversion")

    args = parser.parse_args()

    image_size = (args.image_size, args.image_size)

    if args.quantization == "all":
        results = convert_all_variants(
            args.model_path,
            args.output_dir,
            args.representative_data,
            image_size,
        )

        if args.benchmark:
            print("\n" + "=" * 50)
            print("Benchmarks")
            print("=" * 50)
            for quant_type, info in results.items():
                benchmark_tflite(info["tflite_path"])
    else:
        output_path = Path(args.output_dir) / f"{Path(args.model_path).stem}_{args.quantization}.tflite"
        info = convert_to_tflite(
            args.model_path,
            str(output_path),
            args.quantization,
            args.representative_data,
            image_size,
        )

        if args.benchmark:
            benchmark_tflite(info["tflite_path"])


if __name__ == "__main__":
    main()
