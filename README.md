# SmartCrackLens

## Full-Stack Semantic Segmentation for Structural Health Monitoring

A high-performance asynchronous API for structural health monitoring. This backend leverages **Computer Vision (YOLOv8-Segmentation)** to detect, measure, and classify cracks in various surfaces like concrete, metal, and asphalt.

SmartCrackLens is an end-to-end Computer Vision solution designed to automate the detection and localization of surface fractures. By leveraging state-of-the-art Deep Learning, this application transforms raw visual data into actionable structural insights through real-time instance segmentation.

##  Deep Learning Model Training and Instance Segmentation Architecture

SmartCrackLens is built upon a fine-tuned YOLOv8-nano segmentation model (YOLOv8n-seg), trained specifically for crack detection and instance segmentation in structural surfaces. The training dataset was constructed by combining three independent datasets sourced from Roboflow Universe, totaling approximately 12,973 annotated images after merging, deduplication, and redistribution into a 75/15/10 train/validation/test split. All annotations consist of instance-level polygonal masks representing crack boundaries across diverse surface types including asphalt, concrete, brick, and stone. The model was trained for 60 epochs using a batch size of 32 on a NVIDIA Tesla T4 GPU via Google Colab, leveraging transfer learning from COCO-pretrained YOLOv8n-seg weights. The final model achieved a bounding box mAP50 of 0.897 and a segmentation mask mAP50 of 0.724, with an inference speed of approximately 7.7 milliseconds per image at 640x640 resolution. To address a known limitation of the YOLOv8-nano architecture — its tendency to suppress wide, low-frequency crack patterns due to high-frequency kernel bias in its convolutional layers — a post-processing confidence amplification strategy was implemented. This technique applies a staged logit gain boost to the raw ONNX output tensors before thresholding, artificially elevating detection scores for thick crack instances that would otherwise fall below the confidence threshold, complemented by an aggressive Non-Maximum Suppression IoU threshold of 0.30 and a minimum mask area filter of 500 pixels to suppress false positives introduced by the amplification.

## ONNX Runtime Inference Pipeline and Computer Vision Post-Processing

The trained model was exported from PyTorch to the ONNX format at opset 18, producing a lightweight 12.6 MB inference artifact fully compatible with ONNX Runtime 1.19.x and 1.20.x. The inference pipeline is implemented in Python without any dependency on the Ultralytics or PyTorch libraries at runtime, relying exclusively on ONNXRuntime, OpenCV, and NumPy for all preprocessing and postprocessing operations. The preprocessing stage implements a letterbox transformation identical to the Ultralytics inference pipeline, scaling input images uniformly while preserving aspect ratio and filling padding regions with a neutral gray value of (114, 114, 114), producing a normalized float32 tensor of shape (1, 3, 640, 640). Postprocessing reconstructs full-resolution binary segmentation masks by combining the 32 prototype masks with per-detection coefficients via a dot product operation followed by sigmoid activation and spatial upsampling to the original image dimensions. Geometric analysis is then applied to each reconstructed mask using OpenCV contour detection, minimum-area rectangle fitting, and polygon approximation to extract structural crack metrics including mask area in pixels, maximum width, maximum length, dominant orientation (horizontal, vertical, diagonal, forked, or irregular), and a severity classification (low, medium, or high) derived from area and width thresholds calibrated for 640x640 resolution inference.


## RESTful Backend Architecture with FastAPI, MongoDB, and Containerized Deployment

The SmartCrackLens backend is architected as a production-grade RESTful API built with FastAPI and Python 3.12, following a clean layered architecture that separates routing, service logic, data models, and inference concerns into distinct modules. Authentication is implemented using JSON Web Tokens signed with the HS256 algorithm and bcrypt password hashing, providing stateless per-request authorization across all protected endpoints. Persistent storage is handled by MongoDB 7.0 through the Motor asynchronous driver, replacing traditional relational schemas with a document-oriented data model composed of four collections — users, locations, images, and detections — where each detection document embeds an array of crack instance subdocuments containing the full segmentation polygon, bounding box coordinates, confidence score, geometric metrics, and severity classification. This schema design eliminates the need for expensive join operations when retrieving complete inference results, a significant advantage given the nested and variable-length nature of segmentation mask data. The entire application stack is containerized using Docker Compose, defining two isolated services — the FastAPI backend (smartcracklens) and the MongoDB instance (crackdb) — connected through a dedicated internal bridge network (cracknet), with persistent named volumes ensuring data durability across container restarts. An analytics service layer exposes aggregated metrics through dedicated endpoints, executing MongoDB aggregation pipelines that compute severity distributions, surface type breakdowns, orientation radar data, and daily detection timelines, all pre-shaped for direct consumption by Recharts components in the React TypeScript frontend dashboard.

## Fractal Dimension Computing

The fractal dimension (FD) of each detected crack is computed at inference time using the Box-Counting method applied directly to the reconstructed binary segmentation mask produced by the ONNX decoder. Rather than operating on the simplified polygon approximation stored in the database, the algorithm operates on the full-resolution binary raster mask to preserve maximum geometric detail. The implementation is fully vectorized using NumPy — the mask is padded to dimensions divisible by the current box size, reshaped into a four-dimensional block structure, and reduced via any() across spatial axes, eliminating the nested Python loops present in naive Box-Counting implementations and achieving a 50x to 100x speedup suitable for real-time inference. Box counts are collected across a logarithmic scale range derived from powers of two, from floor(log2(min_dimension)) down to scale 2, and a linear regression is fitted to the log-log relationship between box size and count, with the resulting slope representing the fractal dimension clamped to the physically meaningful range [1.0, 2.0]. The computed FD feeds directly into the composite severity classifier alongside mask area and maximum width: values below 1.2 indicate a simple tensile crack with low structural risk, values between 1.2 and 1.4 suggest branching patterns consistent with material failure in multiple directions, and values above 1.4 denote highly tortuous crack geometry associated with severe concrete degradation. An additional escalation rule automatically upgrades the severity classification by one level when the crack orientation is identified as forked — multiple disjointed contours in the binary mask constitute independent geometric evidence of structural branching regardless of the computed FD score.

## Core Engine & Performance

The heart of the project is a YOLOv8-nano-seg model, fine-tuned specifically for high-precision crack detection. The model achieves a sophisticated balance between inference speed and accuracy, making it ideal for deployment in web environments.

* Training Infrastructure: Optimized on NVIDIA T4 GPUs (Google Colab).
* Training Duration: 4h 50m of rigorous fine-tuning.
* Detection Accuracy: mAP50 > 0.86
* Segmentation Accuracy: mAP50-Mask ≈ 0.82

## Key Features

* **Semantic Masking**: Goes beyond simple bounding boxes to provide pixel-level localization of cracks.
* **Full-Stack Integration**: A seamless bridge between a Deep Learning backend and a responsive web interface.
* **Optimized Inference**: Powered by the "nano" architecture to ensure low-latency performance without overlooking structural detail, It runs a quantized **YOLOv8-nano-seg** model via **ONNX Runtime**, ensuring sub-100ms inference on CPU and ultra-fast performance on CUDA.
* **Structural Intelligence**: Beyond simple detection, the engine calculates:
  - **Crack Severity**: Automated classification (Low, Medium, High) based on area and width.
  - **Geometric Metrics**: Extracts length, max width, and orientation (Vertical, Horizontal, Diagonal, Forked).
* **Production Ready**: Fully containerized with **Docker Compose**, including health checks and persistent volume management.
* **Smart Re-analysis**: Capability to re-process existing images when model versions are updated without re-uploading raw data.


## Tech Stack

- **AI/ML**: YOLOv8 (Ultralytics), PyTorch, Computer Vision.
- **Language**: Python 3.12
- **Framework**: FastAPI (Asynchronous)
- **AI/ML**: ONNX Runtime, OpenCV, NumPy
- **Database**: MongoDB (NoSQL)
- **Environment**: Docker & Docker Compose
- **Validation**: Pydantic v2 (Settings & Schemas)


##  Architecture Overview

The project follows **Clean Architecture** principles:
- `app/core`: Application bootstrap, ONNX session Singleton, and global configurations.
- `app/services`: Domain logic including the `InferenceEngine` and `ImageService`.
- `app/models`: ODM-style Pydantic models for MongoDB persistence.
- `app/utils`: Mathematical modules for mask reconstruction and geometry metrics.

## AI Pipeline Details

1. **Pre-processing**: Implements **Letterboxing** to maintain aspect ratio, followed by normalization to $[0, 1]$.
2. **Inference**: Executes the YOLOv8-seg graph.
3. **Mask Reconstruction**: A custom "Hack Trick" implementation of the sigmoid-based decoder to handle ultra-thin cracks that standard NMS might overlook.
4. **Post-processing**:
   - **NMS (Non-Maximum Suppression)** to eliminate duplicates.
   - **Polygon Approximation**: Simplifies complex masks into lightweight JSON-friendly polygons for frontend rendering.

## Getting Started

### Prerequisites
- Docker & Docker Compose
- A `.env` file (see `.env.example`)
```bash
docker-compose up --build
```
Access the interactive API docs at:
http://localhost:8001/docs

## Evaluation Logic
Cracks are evaluated using a weighted matrix of Pixel Area and Max Width.
High Severity: Area > 15,000px OR Width > 60px.
Medium Severity: Area > 5,000px OR Width > 20px.
Low Severity: Surface-level defects.