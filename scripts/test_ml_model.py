from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import os 

# Paths relative to repo root (works no matter where you run from, e.g. /app in Docker)
_REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = _REPO_ROOT / "ml" / "crack_detection_model.onnx"
#IMAGE_PATH = _REPO_ROOT / "privates" / "crack_wall_01.jpg" 
IMAGE_PATH = '../crack_05.jpeg'
OUTPUT_PATH = "output5.jpg"
CONF_THRESHOLD = 0.25

def run_test():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(IMAGE_PATH):
        print("Error: Missing model or image file.")
        return

    # 1. Load Session
    session = ort.InferenceSession(MODEL_PATH, providers=['CPUExecutionProvider'])
    input_info = session.get_inputs()[0]
    input_name = input_info.name
    # YOLOv8 usually [1, 3, 640, 640]
    _, _, h_model, w_model = input_info.shape 

    # 2. Preprocess
    img = cv2.imread(IMAGE_PATH)
    h_orig, w_orig = img.shape[:2]
    
    # Resize and Normalize
    input_img = cv2.resize(img, (w_model, h_model))
    input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
    input_img = input_img.transpose(2, 0, 1).astype(np.float32) / 255.0
    input_img = np.expand_dims(input_img, axis=0)

    # 3. Inference
    outputs = session.run(None, {input_name: input_img})
    
    # YOLOv8-seg output[0] shape is usually [1, 32 + 4 + num_classes, 8400]
    # We will focus on the bounding boxes (first 4 rows) and scores
    predictions = np.squeeze(outputs[0])
    predictions = predictions.T # Shape: [8400, 36+]

    # 4. Post-process (Boxes only for simplicity in pure ONNX)
    boxes = []
    confidences = []
    
    for pred in predictions:
        score = 1.8  * pred[4] # First class score (Crack)
        if score > CONF_THRESHOLD:
            # Scale coordinates back to original image size
            x, y, w, h = pred[0:4]
            x1 = int((x - w/2) * (w_orig / w_model))
            y1 = int((y - h/2) * (h_orig / h_model))
            width = int(w * (w_orig / w_model))
            height = int(h * (h_orig / h_model))
            
            boxes.append([x1, y1, width, height])
            confidences.append(float(score))

    # 5. Non-Maximum Suppression (NMS) to remove overlaps
    indices = cv2.dnn.NMSBoxes(boxes, confidences, CONF_THRESHOLD, 0.45)

    # 6. Draw and Save
    if len(indices) > 0:
        print(f"Detected {len(indices)} crack(s). Drawing...")
        for i in indices.flatten():
            x, y, w, h = boxes[i]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(img, f"Crack {confidences[i]:.2f}", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    else:
        print("No cracks detected.")

    cv2.imwrite(OUTPUT_PATH, img)
    print(f"Inference finished. Results saved in: {OUTPUT_PATH}")




if __name__ == "__main__":
    run_test()
