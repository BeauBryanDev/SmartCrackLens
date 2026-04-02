# SmartCrackLens

## Full-Stack Semantic Segmentation for Structural Health Monitoring

A high-performance asynchronous API for structural health monitoring. This backend leverages **Computer Vision (YOLOv8-Segmentation)** to detect, measure, and classify cracks in various surfaces like concrete, metal, and asphalt.

SmartCrackLens is an end-to-end Computer Vision solution designed to automate the detection and localization of surface fractures. By leveraging state-of-the-art Deep Learning, this application transforms raw visual data into actionable structural insights through real-time instance segmentation.

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