from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.detections import SurfaceType, Orientation, Severity



# CrackInstanceResponse  -SIngle Crack Wall in Response

class CrackInstanceResponse( BaseModel ) :
    
    """ 
    Depict a single crack in client response
    """
    crack_index: int = Field(..., description="Indice de la grieta. Empieza en 0.")
    confidence: float = Field(..., description="Score de confianza. 0.0 a 1.0")
    bbox: list[int] = Field(
        ...,
        description="Bounding box [x1, y1, x2, y2] en pixeles absolutos"
    )
    mask_polygon: list[list[float]] = Field(
        ...,
        description="Poligono de mascara. Lista de pares [x, y] normalizados 0.0-1.0"
    )
    mask_area_px: int = Field(..., description="Area de la mascara en pixeles")
    max_width_px: Optional[int] = Field(default=None, description="Ancho maximo en pixeles")
    max_length_px: Optional[int] = Field(default=None, description="Longitud maxima en pixeles")
    orientation: Optional[Orientation] = Field(default=None, description="Orientacion dominante")
    severity: Optional[Severity] = Field(default=None, description="Severidad: low | medium | high")
    fractal_dimension:  Optional[float] = Field(
        default=None,
        description="Fractal dimension [1.0-2.0]. FD<1.2 simple, 1.2-1.4 branching, FD>1.4 severe."
    )
    
    model_config = {
        "use_enum_values": True,
        "json_schema_extra": {
            "example": {
                "crack_index": 0,
                "confidence": 0.87,
                "bbox": [120, 45, 380, 290],
                "mask_polygon": [
                    [0.512, 0.433], [0.521, 0.445],
                    [0.533, 0.448], [0.548, 0.461],
                ],
                "mask_area_px": 1842,
                "max_width_px": 12,
                "max_length_px": 96,
                "orientation": "diagonal",
                "severity": "medium",
            }
        }
    }
    

# DetectionResponse -Complete Response from a detection

class DetectionResponse(  BaseModel ) :
    
    """
        Complete public response
        POST /api/v1/inference/analyze   
        GET  /api/v1/detections/{id}      
        GET  /api/v1/detections       
    """
    
    id: str = Field(..., description="MongoDB ObjectId como string")
    image_id: str = Field(..., description="ID de la imagen analizada")
    user_id: str = Field(..., description="ID del usuario propietario")
    filename: str = Field(..., description="Nombre original del archivo")
    surface_type: SurfaceType = Field(..., description="Tipo de superficie inspeccionada")
    image_width: int = Field(..., description="Ancho de la imagen en pixeles")
    image_height: int = Field(..., description="Alto de la imagen en pixeles")
    inference_ms: float = Field(..., description="Tiempo de inferencia en milisegundos")
    total_cracks: int = Field(..., description="Total de grietas detectadas")
    detections: list[CrackInstanceResponse] = Field(
        default_factory=list,
        description="Lista de grietas detectadas. Vacia si no hay grietas."
    )
    detected_at: datetime = Field(..., description="Timestamp de la deteccion")

    # Campos calculados — helpers para el frontend
    has_cracks: bool = Field(..., description="True si se detecto al menos una grieta")
    highest_severity: Optional[str] = Field(
        default=None,
        description="Severidad mas alta entre todas las instancias detectadas"
    )
    average_confidence: Optional[float] = Field(
        default=None,
        description="Confianza promedio de todas las detecciones"
    )

    model_config = {
        "use_enum_values": True,
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "id": "661f1e2b3f4a5c6d7e8f9a0b",
                "image_id": "661f1e2b3f4a5c6d7e8f9a0c",
                "user_id": "661f1e2b3f4a5c6d7e8f9a0d",
                "filename": "wall_photo.jpg",
                "surface_type": "asphalt",
                "image_width": 640,
                "image_height": 640,
                "inference_ms": 17.7,
                "total_cracks": 2,
                "has_cracks": True,
                "highest_severity": "medium",
                "average_confidence": 0.80,
                "detections": [
                    {
                        "crack_index": 0,
                        "confidence": 0.87,
                        "bbox": [120, 45, 380, 290],
                        "mask_polygon": [
                            [0.512, 0.433], [0.521, 0.445],
                            [0.533, 0.448], [0.548, 0.461],
                        ],
                        "mask_area_px": 1842,
                        "max_width_px": 12,
                        "max_length_px": 96,
                        "orientation": "diagonal",
                        "severity": "medium",
                        "fractal_dimension": 1.35
                    },
                    {
                        "crack_index": 1,
                        "confidence": 0.73,
                        "bbox": [400, 100, 600, 350],
                        "mask_polygon": [
                            [0.712, 0.233], [0.721, 0.245],
                        ],
                        "mask_area_px": 934,
                        "max_width_px": 8,
                        "max_length_px": 42,
                        "orientation": "diagonal",
                        "severity": "low",
                        "fractal_dimension": 1.16,
                    },
                ],
                "detected_at": "2026-03-27T15:35:25",
            }
        }
    }
    
    @classmethod
    def from_mongo(cls, document: dict) -> "DetectionResponse":
        """
        Convierte un documento crudo de MongoDB a DetectionResponse.
        Construye los CrackInstanceResponse desde la lista embebida.
        """
        detections = [
            CrackInstanceResponse(
                **instance,
                fractal_dimension=instance.get("fractal_dimension")
                )
            for instance in document.get("detections", [])
        ]

        # Calcular campos derivados directamente aqui
        has_cracks = len(detections) > 0

        priority = {Severity.HIGH: 3, Severity.MEDIUM: 2, Severity.LOW: 1}
        severities = [
            inst.severity for inst in detections
            if inst.severity is not None
        ]
        highest_severity = max(
            severities,
            key=lambda s: priority.get(s, 0),
            default=None
        )

        average_confidence = None
        if detections:
            average_confidence = round(
                sum(inst.confidence for inst in detections) / len(detections),
                4,
            )

        return cls(
            id=str(document["_id"]),
            image_id=str(document["image_id"]),
            user_id=str(document["user_id"]),
            filename=document["filename"],
            surface_type=document["surface_type"],
            image_width=document["image_width"],
            image_height=document["image_height"],
            inference_ms=document["inference_ms"],
            total_cracks=document.get("total_cracks", 0),
            detections=detections,
            detected_at=document["detected_at"],
            has_cracks=has_cracks,
            highest_severity=highest_severity,
            average_confidence=average_confidence,
        )


# DetectionList — response paginado para GET /api/v1/detections

class DetectionList(BaseModel):
    """
    Response paginado para listar detecciones de un usuario.
    Soporta filtrado por surface_type y severity desde el router.
    """
    total: int = Field(..., description="Total de detecciones del usuario")
    page: int = Field(..., description="Pagina actual")
    page_size: int = Field(..., description="Items por pagina")
    results: list[DetectionResponse] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 15,
                "page": 1,
                "page_size": 10,
                "results": [],
            }
        }
    }
    
    
# DetectionDeleted — response 410 Gone para DELETE /api/v1/detections/{id}

class DetectionDeleted(BaseModel):
    """
    Response confirmando la eliminacion de una deteccion.
    HTTP 410 Gone.
    """
    message: str = Field(default="Deteccion eliminada correctamente.")
    deleted_id: str = Field(..., description="ID de la deteccion eliminada")
    deleted_at: datetime = Field(..., description="Timestamp de la eliminacion")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Deteccion eliminada correctamente.",
                "deleted_id": "661f1e2b3f4a5c6d7e8f9a0b",
                "deleted_at": "2026-03-27T15:35:25",
            }
        }
    }


# SurfaceTypeList — response para GET /api/v1/detections/surface-types

class SurfaceTypeList(BaseModel):
    """
    Lista de surface types disponibles.
    El frontend la usa para poblar el dropdown al momento del upload.
    """
    surface_types: list[str] = Field(
        default_factory=lambda: [s.value for s in SurfaceType]
    )
    
    