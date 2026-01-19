"""
Base class for all vision models.
Provides common interface for training, inference, and TFLite conversion.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import tensorflow as tf
from PIL import Image
import structlog

logger = structlog.get_logger()


class BaseVisionModel(ABC):
    """Abstract base class for vision models."""

    def __init__(
        self,
        model_name: str,
        input_size: Tuple[int, int] = (224, 224),
        num_classes: Optional[int] = None,
    ):
        self.model_name = model_name
        self.input_size = input_size
        self.num_classes = num_classes
        self.model: Optional[tf.keras.Model] = None
        self.tflite_interpreter: Optional[tf.lite.Interpreter] = None
        self._class_names: List[str] = []

    @property
    def class_names(self) -> List[str]:
        return self._class_names

    @abstractmethod
    def build_model(self) -> tf.keras.Model:
        """Build and return the Keras model architecture."""
        pass

    @abstractmethod
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for model input."""
        pass

    @abstractmethod
    def postprocess_output(self, output: np.ndarray) -> Dict[str, Any]:
        """Postprocess model output to human-readable format."""
        pass

    def load_image(self, image_path: str | Path) -> np.ndarray:
        """Load and resize image from path."""
        img = Image.open(image_path).convert("RGB")
        img = img.resize(self.input_size, Image.Resampling.LANCZOS)
        return np.array(img)

    def load_image_from_bytes(self, image_bytes: bytes) -> np.ndarray:
        """Load and resize image from bytes."""
        from io import BytesIO

        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img = img.resize(self.input_size, Image.Resampling.LANCZOS)
        return np.array(img)

    def predict(self, image: np.ndarray) -> Dict[str, Any]:
        """Run inference on a single image using Keras model."""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")

        preprocessed = self.preprocess_image(image)
        batch = np.expand_dims(preprocessed, axis=0)

        output = self.model.predict(batch, verbose=0)
        return self.postprocess_output(output[0])

    def predict_tflite(self, image: np.ndarray) -> Dict[str, Any]:
        """Run inference using TFLite interpreter (optimized for mobile/edge)."""
        if self.tflite_interpreter is None:
            raise ValueError("TFLite model not loaded. Call load_tflite() first.")

        preprocessed = self.preprocess_image(image)
        batch = np.expand_dims(preprocessed, axis=0).astype(np.float32)

        input_details = self.tflite_interpreter.get_input_details()
        output_details = self.tflite_interpreter.get_output_details()

        self.tflite_interpreter.set_tensor(input_details[0]["index"], batch)
        self.tflite_interpreter.invoke()

        output = self.tflite_interpreter.get_tensor(output_details[0]["index"])
        return self.postprocess_output(output[0])

    def predict_batch(self, images: List[np.ndarray]) -> List[Dict[str, Any]]:
        """Run inference on a batch of images."""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")

        preprocessed = np.array([self.preprocess_image(img) for img in images])
        outputs = self.model.predict(preprocessed, verbose=0)

        return [self.postprocess_output(out) for out in outputs]

    def load_model(self, model_path: str | Path) -> None:
        """Load Keras model from path."""
        self.model = tf.keras.models.load_model(model_path)
        logger.info("model_loaded", model_name=self.model_name, path=str(model_path))

    def load_tflite(self, tflite_path: str | Path) -> None:
        """Load TFLite model from path."""
        self.tflite_interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
        self.tflite_interpreter.allocate_tensors()
        logger.info(
            "tflite_model_loaded", model_name=self.model_name, path=str(tflite_path)
        )

    def save_model(self, save_path: str | Path) -> None:
        """Save Keras model to path."""
        if self.model is None:
            raise ValueError("No model to save. Build or load a model first.")

        self.model.save(save_path)
        logger.info("model_saved", model_name=self.model_name, path=str(save_path))

    def convert_to_tflite(
        self,
        save_path: str | Path,
        quantize: bool = True,
        representative_dataset: Optional[callable] = None,
    ) -> None:
        """
        Convert Keras model to TFLite format.

        Args:
            save_path: Path to save the .tflite file
            quantize: Whether to apply int8 quantization (reduces size ~4x)
            representative_dataset: Generator function for quantization calibration
        """
        if self.model is None:
            raise ValueError("No model to convert. Build or load a model first.")

        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)

        if quantize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]

            if representative_dataset:
                converter.representative_dataset = representative_dataset
                converter.target_spec.supported_ops = [
                    tf.lite.OpsSet.TFLITE_BUILTINS_INT8
                ]
                converter.inference_input_type = tf.uint8
                converter.inference_output_type = tf.uint8
                logger.info("applying_full_integer_quantization")
            else:
                logger.info("applying_dynamic_range_quantization")

        tflite_model = converter.convert()

        with open(save_path, "wb") as f:
            f.write(tflite_model)

        # Log size comparison
        original_size = sum(
            w.numpy().nbytes for w in self.model.trainable_weights
        ) / (1024 * 1024)
        tflite_size = len(tflite_model) / (1024 * 1024)

        logger.info(
            "tflite_converted",
            model_name=self.model_name,
            original_size_mb=f"{original_size:.2f}",
            tflite_size_mb=f"{tflite_size:.2f}",
            compression_ratio=f"{original_size / tflite_size:.1f}x",
            path=str(save_path),
        )

    def get_model_info(self) -> Dict[str, Any]:
        """Get model metadata and statistics."""
        info = {
            "model_name": self.model_name,
            "input_size": self.input_size,
            "num_classes": self.num_classes,
            "class_names": self._class_names,
        }

        if self.model:
            info["keras_model"] = {
                "trainable_params": sum(
                    np.prod(w.shape) for w in self.model.trainable_weights
                ),
                "total_params": self.model.count_params(),
            }

        if self.tflite_interpreter:
            input_details = self.tflite_interpreter.get_input_details()
            output_details = self.tflite_interpreter.get_output_details()
            info["tflite_model"] = {
                "input_shape": input_details[0]["shape"].tolist(),
                "output_shape": output_details[0]["shape"].tolist(),
                "input_dtype": str(input_details[0]["dtype"]),
                "output_dtype": str(output_details[0]["dtype"]),
            }

        return info
