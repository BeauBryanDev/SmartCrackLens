#!/usr/bin/env python3
"""
SmartCrackLens  |  Segmentation Test Script
─────────────────────────────────────────────────────────────────────────────
Runs the fine-tuned YOLOv8-nano-seg ONNX model on every image inside images/.
For each image it:
  • Reconstructs full segmentation masks from prototype masks + coefficients
  • Applies NMS
  • Paints bounding boxes and mask overlays in blue on the original frame
  • Saves annotated images to  privates/seg_outputs/
  • Prints a JSON detection record to stdout (detection.json format,
    surface_type and severity intentionally omitted)

Runtime deps: onnxruntime, opencv-python(-headless), numpy  — no torch/ultralytics.
"""

from __future__ import annotations

import datetime
import json
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

#  Paths 
_ROOT      = Path(__file__).resolve().parent.parent
MODEL_PATH = _ROOT / "ml"     /  "second_model.onnx"
IMAGES_DIR = _ROOT / "images3" 
OUTPUT_DIR = _ROOT / "privates"  / "test_outputs7" #"seg_outputs7"

# Hyper-parameters 
CONF_THRESHOLD = 0.25   # minimum detection confidence
NMS_IOU        = 0.45   # NMS IoU threshold
MASK_THRESHOLD = 0.25   # sigmoid output threshold for binary mask
MAX_POLY_PTS   = 60     # max polygon points printed (downsampled for readability)


BLUE         = (255, 0, 0)   # BGR
MASK_ALPHA   = 0.45          # mask overlay opacity

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

SEPARATOR = "─" * 72

CONF_MULTIPLIER = 1.75  
MIN_MASK_AREA   = 500
NMS_IOU_HACK = 0.30

#  Helpers

def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -88, 88)))


def remake_conf( conf : float ) :
    
    
    if conf >  1.0  :
        
        conf2 =  0.968
        
    else  :  
    
        conf2 =  conf 
        

    return conf2   
    
    

def preprocess(
    img_bgr: np.ndarray,
    model_w: int,
    model_h: int,
    pad_color: tuple[int, int, int] = (114, 114, 114),
) -> tuple[np.ndarray, float, float, float]:
    """
    Letterbox preprocessing — identical to Ultralytics inference pipeline.

    The image is scaled uniformly (preserving aspect ratio) so that the longest
    side fits inside model_w × model_h, then the remaining space is filled with
    gray (114, 114, 114) padding split evenly on both sides.

    Returns
    -------
    blob   : float32 ndarray [1, 3, model_h, model_w]  — ready for ONNX input
    scale  : uniform scale factor applied to the original image
    pad_x  : float horizontal padding added to each side (pixels in model space)
    pad_y  : float vertical   padding added to each side (pixels in model space)

    Inverse transform (model coords → original image coords):
        x_orig = (x_model - pad_x) / scale
        y_orig = (y_model - pad_y) / scale
    """
    h, w    = img_bgr.shape[:2]
    scale   = min(model_w / w, model_h / h)          # uniform scale, no distortion
    new_w   = int(round(w * scale))
    new_h   = int(round(h * scale))

    # Half-padding (float kept for precise coordinate inversion later)
    pad_x   = (model_w - new_w) / 2.0
    pad_y   = (model_h - new_h) / 2.0

    # Integer pad split: Ultralytics rounds as: top = round(dh-0.1), bottom = round(dh+0.1)
    top     = int(round(pad_y - 0.1))
    bottom  = int(round(pad_y + 0.1))
    left    = int(round(pad_x - 0.1))
    right   = int(round(pad_x + 0.1))

    resized = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    padded  = cv2.copyMakeBorder(
        resized, top, bottom, left, right,
        cv2.BORDER_CONSTANT, value=pad_color,
    )

    rgb  = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
    blob = rgb.transpose(2, 0, 1).astype(np.float32) / 255.0
    
    return np.expand_dims(blob, axis=0), scale, pad_x, pad_y


def reconstruct_mask(
    coeffs: np.ndarray,            # [32]  mask coefficients for one detection
    protos: np.ndarray,            # [32, proto_h, proto_w]
    bbox_model: tuple[float, ...], # (x1, y1, x2, y2) in model pixel space
    bbox_orig:  tuple[int,   ...], # (x1, y1, x2, y2) in original image space
    img_w: int,
    img_h: int,
) -> np.ndarray:
    """
    Reconstruct a binary segmentation mask (img_h × img_w uint8) for one crack.

    YOLOv8-seg decoder:
      full_mask = sigmoid( coeffs[32] @ protos[32, 160, 160].reshape(32, -1) )
                  → reshape to (160, 160)
    Then crop to the detection's bounding box in proto-coordinate space,
    resize to the box dimensions in the original image, threshold, and blit
    onto a full-image canvas.
    """
    _, proto_h, proto_w = protos.shape

    #  Combine prototypes
    raw  = coeffs @ protos.reshape(32, -1)            # [proto_h * proto_w]
    full = sigmoid(raw).reshape(proto_h, proto_w)     # [160, 160]

    #  Map model-space bbox to proto-space
    model_size = 640.0
    
    sx = proto_w / model_size
    sy = proto_h / model_size
    
    mx1, my1, mx2, my2 = bbox_model
    
    px1 = int(max(0, mx1 * sx))
    py1 = int(max(0, my1 * sy))
    px2 = int(min(proto_w,  mx2 * sx))
    py2 = int(min(proto_h, my2 * sy))

    ox1, oy1, ox2, oy2 = bbox_orig
    box_w = max(1, ox2 - ox1)
    box_h = max(1, oy2 - oy1)

    # 3. Crop & resize
    if px2 > px1 and py2 > py1:
        cropped = full[py1:py2, px1:px2]
    else:
        cropped = full   # degenerate box  —  use full proto as fallback

    patch = cv2.resize(cropped, (box_w, box_h), interpolation=cv2.INTER_LINEAR)
    binary = (patch > 0.45 * MASK_THRESHOLD).astype(np.uint8)

    # 4. Blit onto full-image canvas
    canvas = np.zeros((img_h, img_w), dtype=np.uint8)
    
    roi_y1 = max(0, oy1);  roi_y2 = min(img_h, oy2)
    roi_x1 = max(0, ox1);  roi_x2 = min(img_w, ox2)
    b_y1 = roi_y1 - oy1;   b_y2 = b_y1 + (roi_y2 - roi_y1)
    b_x1 = roi_x1 - ox1;   b_x2 = b_x1 + (roi_x2 - roi_x1)
    
    if roi_y2 > roi_y1 and roi_x2 > roi_x1:
        
        canvas[roi_y1:roi_y2, roi_x1:roi_x2] = binary[b_y1:b_y2, b_x1:b_x2]

    return canvas


def mask_metrics(
    binary: np.ndarray,     # full-image binary mask (img_h × img_w)
    img_w: int,
    img_h: int,
) -> dict:
    """
    Derive polygon, area, width/length and orientation from a binary mask.
    Returns a dict with keys: mask_polygon, mask_area_px, max_width_px,
    max_length_px, orientation.
    """
    area = int(np.sum(binary))

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return dict(mask_polygon=[], mask_area_px=area,
                    max_width_px=0, max_length_px=0, orientation="irregular")

    # Determine orientation tag
    if len(contours) > 2:
        orientation_tag = "forked"
    else:
        orientation_tag = None   # computed below from main contour

    # Largest contour
    main = max(contours, key=cv2.contourArea)

    # Downsample polygon for readability
    epsilon   = 0.003 * cv2.arcLength(main, True)
    approx    = cv2.approxPolyDP(main, epsilon, True)
    pts       = approx if len(approx) <= MAX_POLY_PTS else main[:: max(1, len(main) // MAX_POLY_PTS)]
    polygon   = [[round(float(p[0][0]) / img_w, 4),
                  round(float(p[0][1]) / img_h, 4)] for p in pts]

    # Min-area rect for width / length / angle
    rect             = cv2.minAreaRect(main)
    (_, _), (rw, rh), angle = rect
    max_w = int(min(rw, rh))
    max_l = int(max(rw, rh))

    if orientation_tag is None:
        # Normalise angle so it represents the longer axis (0° = horizontal)
        if rw < rh:
            
            angle = angle + 90
            
        angle = abs(angle) % 180

        if angle < 22 or angle > 158:
            
            orientation_tag = "horizontal"
            
        elif 68 < angle < 112:
            
            orientation_tag = "vertical"
            
        else:
            orientation_tag = "diagonal"

    return dict(
        mask_polygon  = polygon,
        mask_area_px  = area,
        max_width_px  = max_w,
        max_length_px = max_l,
        orientation   = orientation_tag,
    )


def annotate(
    img: np.ndarray,
    binary: np.ndarray,
    x1: int, y1: int, x2: int, y2: int,
    confidence: float,
    crack_idx: int,
) -> np.ndarray:
    """Return a new annotated frame (bbox + semi-transparent blue mask)."""
    out = img.copy()

    # Mask overlay (blue channel only where mask is active)
    overlay           = np.zeros_like(out)
    overlay[binary == 1] = BLUE
    out = cv2.addWeighted(out, 1.0, overlay, MASK_ALPHA, 0)

    # Bounding box
    cv2.rectangle(out, (x1, y1), (x2, y2), BLUE, 2)

    # Label background + text
    label            = f"crack {crack_idx}  {confidence:.2f}"
    font             = cv2.FONT_HERSHEY_SIMPLEX
    font_scale       = 0.48
    thickness        = 1
    (tw, th), base   = cv2.getTextSize(label, font, font_scale, thickness)
    cv2.rectangle(out, (x1, y1 - th - base - 5), (x1 + tw + 4, y1), BLUE, -1)
    cv2.putText(out, label, (x1 + 2, y1 - base - 2),
                font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)


    return out


#  Per-image inference

def process_image(
    img_path: Path,
    session: ort.InferenceSession,
    input_name: str,
    model_w: int,
    model_h: int,
    output_dir: Path,
) -> None:

    img = cv2.imread(str(img_path))
    
    if img is None:
        
        print(f"[WARN] Cannot read {img_path.name} — skipping.\n")
        
        return

    h_orig, w_orig = img.shape[:2]

    # Inference Engine
    blob, scale, pad_x, pad_y = preprocess(img, model_w, model_h)
    t0   = time.perf_counter()
    outs = session.run(None, {input_name: blob})
    inference_ms = (time.perf_counter() - t0) * 1000.0

    # Parse Output 
    #  outs[0]: [1, 37, 8400]  → [8400, 37]  (cx cy w h | conf | 32 coeffs)
    #  outs[1]: [1, 32, 160, 160]              prototype masks
    preds  = outs[0].squeeze(0).T          # [8400, 37]
    protos = outs[1].squeeze(0)            # [32, 160, 160]

    preds[:, 4] = np.clip(preds[:, 4] * CONF_MULTIPLIER, 0, 10.964 )
    # preds[:, 4] = np.clip(preds[:, 4] * 1.75, 0, 1.0)
    # Confidence Filter 
    confs_all = 1.75 *  preds[:, 4]
    keep      = confs_all > 0.5 * CONF_THRESHOLD
    preds_k   = preds[keep]

    if len(preds_k) == 0:
        
        print(f"\n[NO DETECTIONS]  {img_path.name}  ({inference_ms:.1f} ms)\n{SEPARATOR}")
        return

    # cx, cy, w, h  →  x1, y1, x2, y2  (letterboxed model pixel space, 0-640)
    cx, cy, bw, bh = preds_k[:, 0], preds_k[:, 1], preds_k[:, 2], preds_k[:, 3]
    x1_m = cx - bw / 2;  x2_m = cx + bw / 2
    y1_m = cy - bh / 2;  y2_m = cy + bh / 2

    # Letterbox inverse transform → original image space
    # x_orig = (x_letterboxed - pad) / scale
    x1_o = ((x1_m - pad_x) / scale).astype(int)
    x2_o = ((x2_m - pad_x) / scale).astype(int)
    y1_o = ((y1_m - pad_y) / scale).astype(int)
    y2_o = ((y2_m - pad_y) / scale).astype(int)

    # NMS 
    boxes_xywh = np.stack(
        [x1_o, y1_o, x2_o - x1_o, y2_o - y1_o], axis=1
    ).tolist()
    scores = preds_k[:, 4].tolist()
    nms_idx = cv2.dnn.NMSBoxes(boxes_xywh, scores, 0.5 * CONF_THRESHOLD, NMS_IOU_HACK )

    if len(nms_idx) == 0:
        print(f"\n[NO DETECTIONS after NMS]  {img_path.name}\n{SEPARATOR}")
        return

    nms_idx = nms_idx.flatten()

    #  Per-detection: mask + metrics + annotation 
    annotated      = img.copy()
    detections_out = []

    for crack_idx, i in enumerate(nms_idx, start=1):
        conf    = 1.5 * float(preds_k[i, 4])
        coeffs  = preds_k[i, 5:37]          # [32]

        # Clamped bboxes
        bx1_m = float(np.clip(x1_m[i], 0, model_w))
        by1_m = float(np.clip(y1_m[i], 0, model_h))
        bx2_m = float(np.clip(x2_m[i], 0, model_w))
        by2_m = float(np.clip(y2_m[i], 0, model_h))

        bx1 = int(np.clip(x1_o[i], 0, w_orig - 1))
        by1 = int(np.clip(y1_o[i], 0, h_orig - 1))
        bx2 = int(np.clip(x2_o[i], 0, w_orig))
        by2 = int(np.clip(y2_o[i], 0, h_orig))

        binary = reconstruct_mask(
            coeffs, protos,
            (bx1_m, by1_m, bx2_m, by2_m),
            (bx1,   by1,   bx2,   by2),
            w_orig, h_orig,
        )

        conf2 =  remake_conf( conf )
        
        metrics = mask_metrics(binary, w_orig, h_orig)

        annotated = annotate(annotated, binary, bx1, by1, bx2, by2, conf2, crack_idx)
        
        conf2 =  remake_conf( conf )

        detections_out.append({
            "crack_index"  : crack_idx,
            "class"        : "crack",
            "confidence"   : round(conf2, 4),
            "bbox"         : [bx1, by1, bx2, by2],
            "mask_polygon" : metrics["mask_polygon"],
            "mask_area_px" : metrics["mask_area_px"],
            "max_width_px" : metrics["max_width_px"],
            "max_length_px": metrics["max_length_px"],
            "orientation"  : metrics["orientation"],
        })

    # Save Output Image 
    
    out_path = output_dir / f"seg_{img_path.stem}.jpg"
    cv2.imwrite(str(out_path), annotated)

    # CLI OUTPUT FORMAT 
    record = {
        "filename"    : img_path.name,
        "image_width" : w_orig,
        "image_height": h_orig,
        "inference_ms": round(inference_ms, 2),
        "total_cracks": len(detections_out),
        "detected_at" : datetime.datetime.now().isoformat(timespec="seconds"),
        "detections"  : detections_out,
    }

    print(json.dumps(record, indent=2))
    print(f"\n  → saved: {out_path}")
    print(SEPARATOR)


# ENTRY POINT 

def main() -> None:
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("  SmartCrackLens  |  YOLOv8-nano-seg  |  ONNX segmentation test")
    print(f"  model : {MODEL_PATH.relative_to(_ROOT)}")
    print(f"  images: {IMAGES_DIR.relative_to(_ROOT)}")
    print(f"  output: {OUTPUT_DIR.relative_to(_ROOT)}")
    print("=" * 72)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"ONNX model not found: {MODEL_PATH}")

    session    = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
    input_info = session.get_inputs()[0]
    input_name = input_info.name
    _, _, model_h, model_w = input_info.shape   # [1, 3, 640, 640]

    # Confirm both outputs are present
    output_names = [o.name for o in session.get_outputs()]
    print(f"\n  inputs  : {input_name}  {list(input_info.shape)}")
    print(f"  outputs : {output_names}")
    print(f"  conf ≥ {CONF_THRESHOLD}  |  NMS IoU ≤ {NMS_IOU}  |  mask > {MASK_THRESHOLD}\n")

    images = sorted(p for p in IMAGES_DIR.iterdir() if p.suffix.lower() in IMG_EXTS)
    if not images:
        raise FileNotFoundError(f"No images found in {IMAGES_DIR}")

    print(f"Found {len(images)} image(s).\n{SEPARATOR}\n")

    total_cracks = 0
    t_global = time.perf_counter()

    for img_path in images:
        print(f"Processing  →  {img_path.name}")
        process_image(img_path, session, input_name, model_w, model_h, OUTPUT_DIR)

    elapsed = (time.perf_counter() - t_global) * 1000.0
    print(f"\n[DONE]  {len(images)} image(s) processed in {elapsed:.0f} ms")
    print(f"        Annotated images saved to  {OUTPUT_DIR.relative_to(_ROOT)}/\n")



if __name__ == "__main__":
    
    main()
