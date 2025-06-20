import numpy as np
import tensorflow as tf

from typing import Tuple
from PIL import Image
from io import BytesIO

# Singleton instance for TFLite model and its tensor indices
_interpreter: tf.lite.Interpreter = None
_input_index: int = None
_output_index: int = None

def load_model(model_path: str = "src/models/facenet.tflite") -> Tuple[tf.lite.Interpreter, int, int]:
    """
    Load the FaceNet TFLite model and return the interpreter with input/output tensor indices.

    Parameters:
        model_path (str): Path to the TFLite model file.

    Returns:
        Tuple containing:
            - interpreter (tf.lite.Interpreter): The loaded model interpreter.
            - input_index (int): Input tensor index.
            - output_index (int): Output tensor index.
    """
    global _interpreter, _input_index, _output_index

    if _interpreter is None:
        _interpreter = tf.lite.Interpreter(model_path=model_path)
        _interpreter.allocate_tensors()

        _input_index = _interpreter.get_input_details()[0]["index"]
        _output_index = _interpreter.get_output_details()[0]["index"]

    return _interpreter, _input_index, _output_index

interpreter, input_index, output_index = load_model()

def extract_embedding(image_bytes):
    image = Image.open(BytesIO(image_bytes)).resize((160, 160)).convert("RGB")
    img_array = np.asarray(image).astype(np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    interpreter.set_tensor(input_index, img_array)
    interpreter.invoke()
    embedding = interpreter.get_tensor(output_index)
    return embedding[0]