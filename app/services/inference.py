import datetime
import time

import cv2
import numpy as np
import onnxruntime as ort


from app.core.logging import logger

from app.models.detections import CrackInstance, Orientation, Severity

from app.utils.image_utils import annotate_frame, clamp_confidence, preprocess
from app.utils.geometry_utils import (
    MIN_MASK_AREA,
    calculate_severity,
    mask_metrics,
    reconstruct_mask,
)


# Inference hyper-parameters
CONF_THRESHOLD  = 0.25
CONF_MULTIPLIER = 1.75   # stage-1 logit amplification
CONF_STAGE2     = 1.50   # stage-2 amplification applied per detection
NMS_IOU_HACK    = 0.30   # NMS to suppress thick-crack duplicates
MODEL_W         = 640
MODEL_H         = 640


# analyze_image — public entrypoint called by the router

async def analyze_image(
    img_bgr: np.ndarray,
    session: ort.InferenceSession,
    original_filename: str,
    surface_type: str,
) -> dict:
    
    """
    Full Inference Pipeline
    Args :
        img_bgr           : numpy array BGR loaded from disk by storage.py
        session           : ONNX InferenceSession loaded at app startup
        original_filename : used in the response record
        surface_type      : SurfaceType enum value from the upload request    
    Returns:
        dict with keys matching DetectionDocument structure:
        filename, surface_type, image_width, image_height,
        inference_ms, total_cracks, detections, detected_at
        
    Plus:
        annotated_image: np.ndarray BGR with masks drawn (saved by storage.py)
        
    """
    
     h_orig, w_orig = img_bgr.shape[:2]
    logger.info(f"Inference start: {original_filename} | {w_orig}x{h_orig}px")

    # Pre - Processing 
    
    blob, scale, pad_x, pad_y = preprocess(img_bgr, MODEL_W, MODEL_H)
    
    # ONNX Inference 
    
    nput_name = session.get_inputs()[0].name
    
    t0     = time.perf_counter()
    outs   = session.run(None, {input_name: blob})
    
    inference_ms  = (time.perf_counter() - t0) * 1000.0

    logger.info(f"ONNX inference: {inference_ms:.1f} ms")

    preds  = outs[0].squeeze(0).T   # [8400, 37]
    protos = outs[1].squeeze(0)
    
    preds[:, 4] = np.clip(preds[:, 4] * CONF_MULTIPLIER, 0, 10.964)
    
    # Confidence Filtering
    
    confs_all = CONF_MULTIPLIER * preds[:, 4]
    keep    = confs_all > 0.5 * CONF_THRESHOLD
    preds_k  = preds[keep]
    
    if len(preds_k) == 0:
        
        logger.info(f"No detections after confidence filter: {original_filename}")
        
        return _empty_result(original_filename, surface_type, w_orig, h_orig, inference_ms)
    
    
    # cx cy w h -> x1 y1 x2 y2 in model space + inverse letterbox
    
    cx, cy, bw, bh = preds_k[:, 0], preds_k[:, 1], preds_k[:, 2], preds_k[:, 3]

    x1_m = cx - bw / 2;  x2_m = cx + bw / 2
    y1_m = cy - bh / 2;  y2_m = cy + bh / 2

    # Inverse letterbox transform -> original image space
    x1_o = ((x1_m - pad_x) / scale).astype(int)
    x2_o = ((x2_m - pad_x) / scale).astype(int)
    y1_o = ((y1_m - pad_y) / scale).astype(int)
    y2_o = ((y2_m - pad_y) / scale).astype(int)
    
    # NMS  for thick cracks
    
    boxes_xywh = np.stack(
        
        [x1_o, y1_o, x2_o - x1_o, y2_o - y1_o], axis=1
    ).tolist()
    
    scores  = preds_k[:, 4].tolist()
    
    nms_idx = cv2.dnn.NMSBoxes(
        
        boxes_xywh, scores,
        0.5 * CONF_THRESHOLD,
        NMS_IOU_HACK,
    )
    
    if len(nms_idx) == 0:
        
        logger.info(f"No detections after NMS: {original_filename}")
        return _empty_result(original_filename, surface_type, w_orig, h_orig, inference_ms)

    nms_idx = nms_idx.flatten()
    
    # Per-detection: mask + metrics + severity + annotation
    
    annotated      = img_bgr.copy()
    detections_out: list[CrackInstance] = []
    
    for crack_idx, i in enumerate(nms_idx, start=1):

        conf   = clamp_confidence(CONF_STAGE2 * float(preds_k[i, 4]))
        coeffs = preds_k[i, 5:37]   # [32] mask coefficients

        bx1_m = float(np.clip(x1_m[i], 0, MODEL_W))
        by1_m = float(np.clip(y1_m[i], 0, MODEL_H))
        bx2_m = float(np.clip(x2_m[i], 0, MODEL_W))
        by2_m = float(np.clip(y2_m[i], 0, MODEL_H))

        bx1 = int(np.clip(x1_o[i], 0, w_orig - 1))
        by1 = int(np.clip(y1_o[i], 0, h_orig - 1))
        bx2 = int(np.clip(x2_o[i], 0, w_orig))
        by2 = int(np.clip(y2_o[i], 0, h_orig))

        # Mask reconstruction with lowered sigmoid threshold
        binary = reconstruct_mask(
            coeffs, protos,
            (bx1_m, by1_m, bx2_m, by2_m),
            (bx1,   by1,   bx2,   by2),
            w_orig, h_orig,
        )
        
        # Filter noise — discard masks smaller than MIN_MASK_AREA
        if int(np.sum(binary)) < MIN_MASK_AREA:
            
            logger.debug(f"Crack {crack_idx} discarded — mask area below MIN_MASK_AREA")
            
            continue
        
        # Geometry metrics from mask contours
        metrics = mask_metrics(binary, w_orig, h_orig)

        # Severity classification
        severity = calculate_severity(
            
            metrics["mask_area_px"],
            metrics["max_width_px"],
        )
        
        # Annotate frame
        annotated = annotate_frame(
            
            annotated, binary,
            bx1, by1, bx2, by2,
            conf, crack_idx,
        )
        
        detections_out.append(CrackInstance(
            
            crack_index   = crack_idx,
            confidence    = round(conf, 4),
            bbox          = [bx1, by1, bx2, by2],
            mask_polygon  = metrics["mask_polygon"],
            mask_area_px  = metrics["mask_area_px"],
            max_width_px  = metrics["max_width_px"],
            max_length_px = metrics["max_length_px"],
            orientation   = metrics["orientation"],
            severity      = severity,
        ))
        
    if not detections_out:
        
        logger.info(f"All detections filtered by MIN_MASK_AREA: {original_filename}")
        
        return _empty_result(original_filename, surface_type, w_orig, h_orig, inference_ms)

    logger.info(
        
        f"Inference complete: {original_filename} | "
        f"cracks: {len(detections_out)} | "
        f"{inference_ms:.1f} ms"
    )
    
    return {
        
        "filename"  : original_filename,
        "surface_type" : surface_type,
        "image_width"  : w_orig,
        "image_height"  : h_orig,
        "inference_ms"  : round(inference_ms, 2),
        "total_cracks" : len(detections_out),
        "detections"  : detections_out,
        "detected_at"  : datetime.datetime.now(datetime.timezone.utc),
        "annotated_image" : annotated,   # np.ndarray BGR — saved by storage.py
    }
    

# Empty Results for Images with not detections 

def _empty_result(
    filename: str,
    surface_type: str,
    image_width: int,
    image_height: int,
    inference_ms: float,
) -> dict:
    
    return {
        "filename"        : filename,
        "surface_type"    : surface_type,
        "image_width"     : image_width,
        "image_height"    : image_height,
        "inference_ms"    : round(inference_ms, 2),
        "total_cracks"    : 0,
        "detections"      : [],
        "detected_at"     : datetime.datetime.now(datetime.timezone.utc),
        "annotated_image" : None,
    }
    
    