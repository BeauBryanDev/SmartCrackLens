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
    rect             = cv2.minAreaRect(main)
    
    (_, _), (rw, rh), angle = rect
    
    max_w = int(min(rw, rh))
    max_l = int(max(rw, rh))
    
    
    if orientation_tag is None:
        
        if rw < rh:
            
            angle = angle + 90
            
        angle = abs(angle) % 180
        

        if angle < 22 or angle > 158:
            
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
    
    
def calculate_severity(mask_area_px: int, max_width_px: int) -> Severity:
    
    """
    Classify crack severity based on mask area and maximum width.

    Rules:
        HIGH   — area > 15000 px  OR  width > 60 px
        MEDIUM — area > 5000  px  OR  width > 20 px
        LOW    — everything else under MEDIUM

    Thresholds calibrated for 640x640 inference resolution.
    Adjust if using higher resolution inputs.
    
    """
    
    if mask_area_px > 15000 or max_width_px > 60:
        
        return Severity.HIGH
    
    elif mask_area_px > 5000 or max_width_px > 20:
        
        return Severity.MEDIUM
    
    else:
        
        return Severity.LOW
    
    