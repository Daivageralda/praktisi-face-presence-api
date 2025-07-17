import threading
import tensorflow as tf

from typing import Tuple
from src.core import settings, logger

# Thread-safe singleton pattern for model loading
_model_lock = threading.Lock()
_interpreter: tf.lite.Interpreter = None
_input_index: int = None
_output_index: int = None

def load_model(model_path: str = settings.MODEL_PATH) -> Tuple[tf.lite.Interpreter, int, int]:
    """
    Load and initialize the TensorFlow Lite model in a thread-safe singleton manner.

    This function ensures the model is only loaded and allocated once, even in multi-threaded environments.
    It also configures TensorFlow threading for optimized performance on low-spec systems.

    Parameters
    ----------
    model_path : str
        The file path to the TensorFlow Lite model (default is from settings).

    Returns
    -------
    Tuple[tf.lite.Interpreter, int, int]
        A tuple containing:
        - the initialized TFLite Interpreter,
        - the input tensor index,
        - the output tensor index.
    """
    global _interpreter, _input_index, _output_index

    if _interpreter is None:
        with _model_lock:
            if _interpreter is None:
                try:
                    tf.config.threading.set_intra_op_parallelism_threads(settings.TF_INTRA_OP_PARALELLISM)
                    tf.config.threading.set_inter_op_parallelism_threads(settings.TF_INTER_OP_PARALELLISM)

                    _interpreter = tf.lite.Interpreter(
                        model_path=str(model_path),
                        num_threads=settings.TF_NUM_THREADS
                    )
                    _interpreter.allocate_tensors()

                    _input_index = _interpreter.get_input_details()[0]["index"]
                    _output_index = _interpreter.get_output_details()[0]["index"]

                    logger.info(f"TFLite model loaded successfully from {model_path}")
                except Exception as e:
                    logger.exception(f"Failed to load TFLite model from {model_path}: {e}")
                    raise

    return _interpreter, _input_index, _output_index

# # Load model on module import
# interpreter, input_index, output_index = load_model()

# def extract_embedding(image_bytes: bytes) -> np.ndarray:
#     """
#     Optimized embedding extraction with memory management and error handling.
    
#     Args:
#         image_bytes: Raw image bytes
        
#     Returns:
#         numpy array of embedding features
#     """
#     try:
#         # Use thread-safe model access
#         with _model_lock:
#             # Validate input
#             if not image_bytes or len(image_bytes) == 0:
#                 raise ValueError("Empty image bytes provided")
                
#             # Preprocess
#             image = Image.open(BytesIO(image_bytes))
            
#             if image.mode != 'RGB':
#                 image = image.convert('RGB')
            
#             image = image.resize((settings.IMAGE_SIZE, settings.IMAGE_SIZE), Image.Resampling.LANCZOS)
#             img_array = np.asarray(image, dtype=np.float32) / 255.0
            
#             if img_array.shape != (settings.IMAGE_SIZE, settings.IMAGE_SIZE, settings.IMAGE_CHANNEL):
#                 raise ValueError(f"Invalid image shape: {img_array.shape}")
            
#             img_array = np.expand_dims(img_array, axis=0)
            
#             # Run Extraction
#             interpreter.set_tensor(input_index, img_array)
#             interpreter.invoke()
#             embedding = interpreter.get_tensor(output_index)
            
#             # Close image to free memory
#             image.close()
            
#             # Validate
#             if embedding is None or embedding.size == 0:
#                 raise ValueError("Empty embedding returned from model")
            
#             embedding_1d = embedding[0] if len(embedding.shape) > 1 else embedding

#             if np.any(np.isnan(embedding_1d)):
#                 raise ValueError("Embedding contains NaN values")
            
#             if np.any(np.isinf(embedding_1d)):
#                 raise ValueError("Embedding contains infinite values")
            
#             return embedding_1d
            
#     except Exception as e:
#         print(f"Error extracting embedding: {e}")
#         return np.zeros(settings.EMBEDDING_DIM, dtype=np.float32)

# import numpy as np
# import tensorflow as tf

# from typing import Tuple
# from PIL import Image
# from io import BytesIO

# # Singleton instance for TFLite model and its tensor indices
# _interpreter: tf.lite.Interpreter = None
# _input_index: int = None
# _output_index: int = None

# def load_model(model_path: str = "src/models/facenet.tflite") -> Tuple[tf.lite.Interpreter, int, int]:
#     """
#     Load the FaceNet TFLite model and return the interpreter with input/output tensor indices.

#     Parameters:
#         model_path (str): Path to the TFLite model file.

#     Returns:
#         Tuple containing:
#             - interpreter (tf.lite.Interpreter): The loaded model interpreter.
#             - input_index (int): Input tensor index.
#             - output_index (int): Output tensor index.
#     """
#     global _interpreter, _input_index, _output_index

#     if _interpreter is None:
#         _interpreter = tf.lite.Interpreter(model_path=model_path)
#         _interpreter.allocate_tensors()

#         _input_index = _interpreter.get_input_details()[0]["index"]
#         _output_index = _interpreter.get_output_details()[0]["index"]

#     return _interpreter, _input_index, _output_index

# interpreter, input_index, output_index = load_model()

# def extract_embedding(image_bytes):
#     image = Image.open(BytesIO(image_bytes)).resize((160, 160)).convert("RGB")
#     img_array = np.asarray(image).astype(np.float32) / 255.0
#     img_array = np.expand_dims(img_array, axis=0)
#     interpreter.set_tensor(input_index, img_array)
#     interpreter.invoke()
#     embedding = interpreter.get_tensor(output_index)
#     return embedding[0]