import onnxruntime as ort
from app.core.config import get_settings
from app.core.logging import logger


settings = get_settings()

_onnx_session: ort.InferenceSession | None = None


def load_model() -> ort.InferenceSession:
    """
    load the ONNX session once in memory.
    Called in the startup event of FastAPI.
    """
    global _onnx_session

    if _onnx_session is not None:
        
        logger.info("ONNX session already loaded, reusing.")
        
        return _onnx_session

    logger.info(f"Loading ONNX model from: {settings.MODEL_PATH}")

    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

    try:
        
        _onnx_session = ort.InferenceSession(
            settings.MODEL_PATH,
            providers=providers,
        )
        
        active_provider = _onnx_session.get_providers()[0]
        input_name = _onnx_session.get_inputs()[0].name
        input_shape = _onnx_session.get_inputs()[0].shape
        input_type = _onnx_session.get_inputs()[0].type
        
        logger.info(f"Model loaded successfully. Active provider: {active_provider}")
        logger.info(f"Input name: {input_name}")
        logger.info(f"Input shape: {input_shape}")
        logger.info(f"Input type: {input_type}")
        
        return _onnx_session
    
    except FileExistsError:
        
        logger.error("Error loading ONNX model")
        logger.error(f"Model path: {settings.MODEL_PATH}")
        logger.error(f"Providers: {providers}")
        raise RuntimeError("Could not load the model")
    
    except Exception as e : 
        
        logger.error(f"Error while loading onnx model : {e}")
        raise RuntimeError(f"Unable to load model {e}")
    
    
def get_oonnx_session() -> ort.InferenceSession:
    
    """
        FastAPI Dep to start ONNX Session service
        
    """
    if _onnx_session is None :
        
        raise RuntimeError("ONNX Model not found, check startup")
    
    return _onnx_session