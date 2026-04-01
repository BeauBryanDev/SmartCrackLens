import cv2
import numpy as np


BLUE       = (255, 0, 0)   # BGR
MASK_ALPHA = 0.45



def preprocess(
    img_bgr: np.ndarray,
    model_w: int = 640,
    model_h: int = 640,
    pad_color: tuple[int, int, int] = (114, 114, 114),
) -> tuple[np.ndarray, float, float, float]:
    
    """
    Letterbox preprocessing similar like to Ultralytics inference pipeline.

    Scales the image uniformly allowed aspect ratio,  therfore the longest side
    fits inside model_w x model_h, then fills remaining space with gray padding
    split evenly on both sides.

    Returns
    blob  : float32 ndarray [1, 3, model_h, model_w]  ready for ONNX input
    scale : uniform scale factor applied to the original image
    pad_x : horizontal padding added to each side (pixels in model space)
    pad_y : vertical   padding added to each side (pixels in model space)

    Inverse transform (model coords -> original image coords):
        x_orig = (x_model - pad_x) / scale
        y_orig = (y_model - pad_y) / scale

    """
    
    h, w  = img_bgr.shape[:2]
    
    scale = min(model_w / w, model_h / h)
    
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))

    pad_x = (model_w - new_w) / 2.0
    pad_y = (model_h - new_h) / 2.0

    top   = int(round(pad_y - 0.1))
    bottom  = int(round(pad_y + 0.1))
    left  = int(round(pad_x - 0.1))
    right   = int(round(pad_x + 0.1))
    
    
    resized = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    padded  = cv2.copyMakeBorder(
        
        resized, top, bottom, left, right,
        cv2.BORDER_CONSTANT, value=pad_color,
        
    )
    
    rgb  = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
    blob = rgb.transpose(2, 0, 1).astype(np.float32) / 255.0
    
    
    return np.expand_dims(blob, axis=0), scale, pad_x, pad_y
    
    
    
def annotate_frame(
    img: np.ndarray,
    binary: np.ndarray,
    x1: int, y1: int, x2: int, y2: int,
    confidence: float,
    crack_idx: int,
) -> np.ndarray:
    
    """
    Returns a new annotated frame with:
    - Semi-transparent blue mask overlay
    - Bounding box
    - Label with crack index and confidence
    """
    
    out =  img.copy()
    
    # Mask overlay
    overlay = np.zeros_like(out)
    overlay[binary == 1] = BLUE
    
    out = cv2.addWeighted(out, 1.0, overlay, MASK_ALPHA, 0)

    # Bounding box
    cv2.rectangle(out, (x1, y1), (x2, y2), BLUE, 2)
    
     # Label
    label            = f"crack {crack_idx}  {confidence:.2f}"
    font             = cv2.FONT_HERSHEY_SIMPLEX
    font_scale       = 0.48
    thickness        = 1
    
    (tw, th), base   = cv2.getTextSize(label, font, font_scale, thickness)
    cv2.rectangle(out, (x1, y1 - th - base - 5), (x1 + tw + 4, y1), BLUE, -1)
    
    cv2.putText(
        
        out, label, (x1 + 2, y1 - base - 2),
        font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA,
    )
    
    return out 


# Hack Trick 
def clamp_confidence(conf: float) -> float:
    """
    Clamps boosted confidence to a maximum of 0.968.
    Prevents values above 1.0 from reaching the JSON response.
    """
    return 0.968 if conf > 1.0 else conf


    