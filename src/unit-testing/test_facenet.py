import os
import pytest
import tensorflow as tf
from src.models.facenet import load_model

def test_load_model_returns_interpreter_and_indices():
    interpreter, input_index, output_index = load_model()

    # Pastikan interpreter adalah instance dari tf.lite.Interpreter
    assert isinstance(interpreter, tf.lite.Interpreter)

    # Pastikan index input dan output berupa integer
    assert isinstance(input_index, int)
    assert isinstance(output_index, int)

def test_facenet_model_file_exists():
    model_path = "src/models/facenet.tflite"
    assert os.path.exists(model_path), f"❌ Model file not found at {model_path}"
