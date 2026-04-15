# SmartCrackLens

![CI](https://github.com/BeauBryanDev/SmartCrackLens/actions/workflows/main.yml/badge.svg)

## Full-Stack Semantic Segmentation for Structural Health Monitoring

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB">
  <img src="https://img.shields.io/badge/YOLOv8-FF0000?style=for-the-badge&logo=ultralytics&logoColor=white" alt="YOLOv8">
  <img src="https://img.shields.io/badge/OpenCV-2496ED?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
  <img src="https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white" alt="Git">
</p>

<div align="center">
  <img src="./frontend/src/assets/crack_detection.svg" alt="crack_detection" width="60%">
</div>

SmartCrackLens is an advanced, end-to-end Computer Vision solution designed to automate the detection, localization, and analysis of surface fractures in structural elements. Built from scratch, the project encompasses the entire MLOps lifecycle—from training a custom YOLOv8 segmentation model to deploying a high-performance full-stack web application.

The core business logic focuses on detecting cracks in surfaces (concrete, metal, asphalt) through real-time instance segmentation, providing actionable structural insights such as crack severity, geometric metrics, and fractal analysis.

---

## Project Structure

```text
.
├── app                     # Backend FastAPI code
│   ├── core                # Global configurations & bootstrap
│   ├── models              # ODM-style Pydantic models for MongoDB
│   ├── routers             # API endpoint definitions
│   ├── schemas             # Pydantic validation schemas
│   ├── services            # Business logic & Inference Engine
│   ├── storage             # Local file storage for images
│   └── utils               # Mathematical & CV utility modules
├── frontend                # Frontend React + Vite code
│   ├── src
│   │   ├── components      # Reusable UI components
│   │   ├── pages           # Main application views (Dashboard, Inference, etc.)
│   │   ├── services        # Axios API clients
│   │   ├── store           # Zustand state management
│   │   └── types           # TypeScript interfaces
├── ml                      # Training artifacts & ONNX models
│   ├── BoxP_curve.png      # Training metrics: Precision
│   ├── BoxPR_curve.png     # Training metrics: Precision-Recall
│   ├── confusion_matrix.png # Model accuracy evaluation
│   ├── results.png         # Overall training losses/metrics
│   ├── val_batch1_pred.jpg # Validation sample predictions
│   └── crack_detection_model.onnx # Fine-tuned inference engine
├── tests                   # Backend & Integration tests
├── docker-compose.yml      # Orchestration for FastAPI & MongoDB
└── requirements.txt        # Python dependencies
```

---

## AI/ML & MLOps Pipeline

### Model Training
The heart of SmartCrackLens is a **fine-tuned YOLOv8-nano segmentation model (YOLOv8n-seg)**, trained on a massive custom dataset of ~13,000 images across diverse surfaces.
- **Training Environment**: Google Colab (NVIDIA Tesla T4 GPU).
- **Training Strategy**: 60 epochs, transfer learning from COCO weights.
- **Optimization**: Post-processing confidence amplification strategy to handle ultra-thin cracks.

### Training Performance Results (Ultralytics)
Below are the key metrics achieved during the fine-tuning process:

<div align="center">

| Metric | Visualization |
| :---: | :---: |
| **Progress Metrics** | ![Results](ml/results.png) |
| **Confusion Matrix** | ![Confusion Matrix](ml/confusion_matrix.png) |
| **Precision Curve** | ![BoxP Curve](ml/BoxP_curve.png) |
| **P-R Curve** | ![BoxPR Curve](ml/BoxPR_curve.png) |
| **Validation Sample** | ![Validation Sample](ml/val_batch1_pred.jpg) |

</div>

---

## Full-Stack Architecture

### Backend (Python/FastAPI)
A production-grade asynchronous REST API built with **FastAPI** (Python 3.12).
- **Inference Core**: Powered by **ONNX Runtime** for CPU/GPU optimized execution, removing the heavy PyTorch dependency at runtime.
- **Computer Vision**: **OpenCV** & **NumPy** for advanced letterboxing, mask reconstruction, and geometric feature extraction.
- **Fractal Computing**: Implements the **Box-Counting method** to calculate crack fractal dimensions (FD), aiding in complex severity classification.
- **Database**: **MongoDB (NoSQL)** for flexible, document-oriented storage of detection metadata and segmentation polygons.
- **Security**: Stateless **JWT Authentication** + **Bcrypt** password hashing.

###  Frontend (React/TypeScript)
A sleek, modern dashboard designed for real-time analysis and visualization.
- **Stack**: React (Functional Components + Hooks) + TypeScript + Vite.
- **Styling**: Tailwind CSS for a responsive, utility-first design.
- **Data Fetching**: **Axios** with interceptors for authenticated API communication.
- **State Management**: **Zustand** for lightweight, performant global state.
- **Visuals**: **Recharts** for rendering analytical radar charts and timeline trends.

---

##  Evaluation Logic & Intelligence
Cracks are not just detected—they are scientifically analyzed:
- **Severity Matrix**: Automated classification (Low, Medium, High) based on Pixel Area and Max Width.
- **Geometric Metrics**: Extraction of length, width, and orientation (Vertical, Horizontal, Diagonal, Forked).
- **Fractal Dimension (FD)**: FD values (1.0 - 2.0) provide insights into the structural degradation severity.

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js (for frontend development)

### Quick Start
1. Clone the repo.
2. Configure `.env` based on `.env.example`.
3. Launch with Docker:
   ```bash
   docker-compose up --build
   4. Access the API at `http://localhost:8001/docs`.
5. Run Frontend:
   cd frontend && npm install && npm run dev
   
---

##  License

<p align="center">MIT License
  <img src="https://img.shields.io/badge/MIT-000000?style=for-the-badge&logo=mit&logoColor=white" alt="MIT">
</p>
