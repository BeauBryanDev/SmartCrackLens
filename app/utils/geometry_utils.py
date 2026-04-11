import cv2
import numpy as np

from app.models.detections import Orientation, Severity


MAX_POLY_PTS   = 60
MASK_THRESHOLD = 0.25
MIN_MASK_AREA  = 500



def sigmoid(x: np.ndarray) -> np.ndarray:
    
    return 1.0 / (1.0 + np.exp(-np.clip(x, -88, 88)))


def reconstruct_mask(
    coeffs: np.ndarray,
    protos: np.ndarray,
    bbox_model: tuple[float, float, float, float],
    bbox_orig:  tuple[int,   int,   int,   int],
    img_w: int,
    img_h: int,
) -> np.ndarray:
    """
    Reconstruct a binary segmentation mask (img_h x img_w uint8) for one crack.

    YOLOv8-seg decoder:
        full_mask = sigmoid( coeffs[32] @ protos[32, 160, 160].reshape(32, -1) )
                    -> reshape to (160, 160)

    Then crops to the detection bounding box in proto-coordinate space,
    resizes to the box dimensions in original image space,
    and blits onto a full-image canvas.
    """
    _, proto_h, proto_w = protos.shape

    # Combine prototypes
    raw  = coeffs @ protos.reshape(32, -1)
    full = sigmoid(raw).reshape(proto_h, proto_w)
    
    # Map model-space bbox to proto-space
    model_size = 640.0
    
    sx = proto_w / model_size
    sy = proto_h / model_size
    
    mx1, my1, mx2, my2 = bbox_model
     
    px1 = int(max(0, mx1 * sx))
    py1 = int(max(0, my1 * sy))
    px2 = int(min(proto_w, mx2 * sx))
    py2 = int(min(proto_h, my2 * sy) ) 
    
    ox1, oy1, ox2, oy2 = bbox_orig
    
    box_w = max(1, ox2 - ox1)
    box_h = max(1, oy2 - oy1)
    
    # Crop and resize
    cropped = full[py1:py2, px1:px2] if (px2 > px1 and py2 > py1) else full
    
    patch   = cv2.resize(cropped, (box_w, box_h), interpolation=cv2.INTER_LINEAR)

    # Lowered threshold — key part of the hack trick for thick cracks
    binary = (patch > 0.45 * MASK_THRESHOLD).astype(np.uint8)
    
    # Blit onto full-image canvas
    canvas  = np.zeros((img_h, img_w), dtype=np.uint8)
    
    roi_y1  = max(0, oy1);  roi_y2 = min(img_h, oy2)
    roi_x1  = max(0, ox1);  roi_x2 = min(img_w, ox2)
    
    b_y1    = roi_y1 - oy1; b_y2   = b_y1 + (roi_y2 - roi_y1)
    b_x1    = roi_x1 - ox1; b_x2   = b_x1 + (roi_x2 - roi_x1)
    
    
    if roi_y2 > roi_y1 and roi_x2 > roi_x1:
        
        canvas[roi_y1:roi_y2, roi_x1:roi_x2] = binary[b_y1:b_y2, b_x1:b_x2]
        
    else :
        
        pass
    

    return canvas


def mask_metrics(
    binary: np.ndarray,
    img_w: int,
    img_h: int,
) -> dict:
    
    """
    Creates polygon, area, width, length and orientation from a binary mask.

    Returns dict with keys:
        mask_polygon, mask_area_px, max_width_px, max_length_px, orientation
    """
    
    area =  int( np.sum( binary) )
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        
        return dict(
            
            mask_polygon=[],
            mask_area_px=area,
            max_width_px=0,
            max_length_px=0,
            orientation=Orientation.IRREGULAR,
        )
    
    # Forked — more than 2 contours means bifurcation in the crack 
    
    orientation_tag = Orientation.FORKED if len(contours) > 2 else None
    
    # Largest contour
    main    = max(contours, key=cv2.contourArea)
    epsilon = 0.003 * cv2.arcLength(main, True)
    approx  = cv2.approxPolyDP(main, epsilon, True)
    
    pts     = (
        approx if len(approx) <= MAX_POLY_PTS
        else main[:: max(1, len(main) // MAX_POLY_PTS)]
    )
    
    polygon = [
        
        [round(float(p[0][0]) / img_w, 4), round(float(p[0][1]) / img_h, 4)]
        for p in pts
    ]
    
    # Min-area rect for width / length / angle
    rect = cv2.minAreaRect(main)
    
    (_, _), (rw, rh), angle = rect
    
    max_w = int(min(rw, rh))
    max_l = int(max(rw, rh))
    
    
    if orientation_tag is None:
        
        if rw < rh:
            
            angle = angle + 90
            
        angle = abs(angle) % 180
        

        if angle < 22 or angle > 160:
            
            orientation_tag = Orientation.HORIZONTAL
            
        elif 68 < angle < 112:
            
            orientation_tag = Orientation.VERTICAL
            
        else:
            
            orientation_tag = Orientation.DIAGONAL
    
    return dict(
        
        mask_polygon=polygon,
        mask_area_px=area,
        max_width_px=max_w,
        max_length_px=max_l,
        orientation=orientation_tag,
    )
    

def _box_count_vectorized(pixels: np.ndarray, scale: int) -> int:
    
    """
    Counts how many boxes of size (scale x scale) contain at least
    one active pixel. Fully vectorized — no Python loops over pixels.

    Pads the array to be divisible by scale, reshapes into a 4D block
    structure, and reduces with any() across the spatial dimensions.
    """
    
    h, w = pixels.shape

    # Pad to make dimensions divisible by scale
    pad_h = (scale - h % scale) % scale
    pad_w = (scale - w % scale) % scale

    padded = np.pad(pixels, ((0, pad_h), (0, pad_w)), mode="constant", constant_values=0)
    ph, pw = padded.shape

    # Reshape into blocks of (scale x scale) and check if any pixel is active
    blocks = padded.reshape(ph // scale, scale, pw // scale, scale)
    filled = blocks.any(axis=(1, 3))

    return int(filled.sum())   

    
# Fractal Dimension — Box-Counting Algorithm (vectorized)

def calculate_fractal_dimension(binary: np.ndarray) -> float:
    
    """
       Computes the fractal dimension (FD) of a crack using the
        Box-Counting method applied directly to the reconstructed binary mask.

        The algorithm covers the binary mask with grids of decreasing box size,
        counts how many boxes contain at least one crack pixel at each scale,
        and fits a linear regression to log(count) vs log(1/scale) to extract
        the fractal dimension as the slope.
    """
    
    pixels = binary > 0

    if not np.any(pixels):
        return 1.0

    # Scale range: powers of 2 from floor(log2(min_dim)) down to 2
    min_dim = min(binary.shape)
    n_max   = int(np.floor(np.log2(min_dim)))

    if n_max < 2:
        return 1.0

    scales = 2 ** np.arange(n_max, 1, -1)
    counts = []

    for scale in scales:
        count = _box_count_vectorized(pixels, scale)
        if count > 0:
            counts.append((scale, count))

    if len(counts) < 2:
        return 1.0

    scales_arr = np.array([c[0] for c in counts], dtype=np.float64)
    counts_arr = np.array([c[1] for c in counts], dtype=np.float64)

    # Linear regression: log(count) = FD * log(1/scale) + constant
    coeffs = np.polyfit(np.log(1.0 / scales_arr), np.log(counts_arr), 1)
    # slope of this line is the fractal dimension
    fd     = float(coeffs[0])

    # Clamp to physically meaningful range [1.0, 2.0]
    fd = max(1.0, min(2.0, fd))

    return round(fd, 2)
    

# Severity Classification - Compostive Score : Combines mask geometry + fractal dimension
    
def calculate_severity(mask_area_px: int,
                       max_width_px: int,
                       fractal_dimension: float,
                       orientation: Orientation,
    ) -> Severity:
    
    """
    Classify crack severity based on mask area and maximum width.

    Rules:
        HIGH   — area > 15000 px  OR  width > 60 px
        MEDIUM — area > 5000  px  OR  width > 20 px
        LOW    — everything else under MEDIUM
        
    Fractal dimension thresholds (civil engineering reference):
        FD < 1.2            simple straight crack — low structural risk
        1.2 <= FD <= 1.4    branching pattern    — moderate risk
        FD > 1.4            tortuous / chaotic   — severe degradation

    Thresholds calibrated for 640x640 inference resolution.
    Adjust if using higher resolution inputs.
    
    """
    
    base_severity =  ''
    
    if  fractal_dimension > 1.4 or mask_area_px > 15000 or max_width_px > 60:
        
        base_severity = Severity.HIGH
    
    elif fractal_dimension > 1.2 or mask_area_px > 5000 or max_width_px > 20:
        
        base_severity = Severity.MEDIUM
    
    else:
        
        base_severity = Severity.LOW
    
    # Forked Escalation rule 
    
    if orientation == Orientation.FORKED:
        
        if base_severity == Severity.LOW:
            
            base_severity = Severity.MEDIUM
            
        elif base_severity == Severity.MEDIUM:
            
            base_severity = Severity.HIGH


    return base_severity