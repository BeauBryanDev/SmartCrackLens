export type Severity = 'low' | 'medium' | 'high';
export type Orientation = 'vertical' | 'horizontal' | 'diagonal' | 'forked';

  
  export interface AuthResponse {

    access_token: string;
    token_type: string;
    user: User;

  }


export interface Detection {

    crack_index: number;
    confidence: number;
    bbox: [number, number, number, number]; // [x, y, w, h]
    mask_polygon: [number, number][]; // Array de coordenadas [x, y]
    mask_area_px: number;
    max_width_px: number;
    max_length_px: number;
    orientation: Orientation;
    severity: Severity;

}

export interface DetectionDocument {

    _id: string;
    image_id: string;
    user_id: string;
    filename: string;
    surface_type: string;
    image_width: number;
    image_height: number;
    inference_ms: number;
    total_cracks: number;
    detections: Detection[];
    detected_at: string; // ISO Date

}


export interface PaginatedUsers {

    items: User[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;

}

export interface User {

    id: string;
    email: string;
    username: string;
    is_admin: boolean;
    country: string;
    is_active : boolean;

}

export interface UserFullUpdate {

    username: string;
    gender: string;
    phone_number: string;
    country: string;
}
  

export interface UserDeleted {

    message: string;
    user_id: string;

}

export type UserPatchUpdate = Partial<Omit<User, 'id' | 'is_admin' | 'email'>>;  

export interface Location {

    id: string;
    user_id: string;
    name: string;
    city: string;
    country: string;
    address: string;
    description?: string;
    created_at: string;
}

export type InferenceStatus = 'processing' | 'completed' | 'failed';


export interface ImageDoc {

    id: string;
    location_id?: string;
    original_filename: string;
    stored_filename: string;
    total_cracks_detected: number;
    inference_status: InferenceStatus;
    inference_ms?: number;
    uploaded_at: string;
    // URLs generadas por el backend
    raw_url: string;
    output_url: string;

}

export interface UserCreate {

    email: string;
    username: string;
    password: string;
    confirm_password: string;
    gender: string;
    phone_number: string;
    country: string;
    
  }
export interface LatencyPoint {

    id: string;
    filename: string;
    latency: number;
    timestamp: string;

}

export interface SeverityData {

    name: Severity;
    value: number; // Cantidad de grietas

}

export interface OrientationData {

    subject: Orientation;
    A: number; // Valor para el RadarChart
    fullMark: number;

}

export interface TimelinePoint {

    date: string; // Formato YYYY-MM-DD
    count: number;

}

export interface ImagePatchUpdate {
   
    location_id: string | null;
}

export interface ImageDeleted {

    message: string;
    image_id: string;
}

export interface PaginatedImages {

    items: ImageDoc[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;

}

export interface UploadInferenceResponse {

    image: ImageDoc;
    detection: DetectionDocument;
    raw_url: string;
    output_url: string;
    output_image_b64: string | null;
}

export interface ImageFilters {

    page?: number;
    pageSize?: number;
    inferenceStatus?: 'completed' | 'processing' | 'failed';
    locationId?: string;
}

export interface LocationCreate {

    name: string;
    city: string;
    country: string;
    address: string;
    description?: string;
}

export interface LocationFullUpdate extends LocationCreate {}

export type LocationPatchUpdate = Partial<LocationCreate>;

export interface PaginatedLocations {

    items: Location[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface LocationDeleted {

    message: string;
    location_id: string;
}

export interface SurfaceTypeList {
    // e.g., {"types": ["wall", "asphalt"]}
    surface_types : string[];

}

export interface PaginatedDetections {

    items: DetectionDocument[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;

}

export interface DetectionDeleted {

    message: string;
    detection_id: string;
 }
  
  export interface DetectionFilters {

    page?: number;
    pageSize?: number;
    surfaceType?: string;
    severity?: Severity;
}

export interface SummaryStats {

    total_images: number;
    total_cracks: number;
    avg_inference_ms: number;
    high_severity_count: number;

}

// For Recharts PieChart
export interface SeverityDistribution {

    data: { name: string; value: number }[];
}

// For Recharts BarChart
export interface SurfaceDistribution {

    data: { name: string; value: number }[];
}

// For Recharts RadarChart
export interface OrientationDistribution {

    data: { subject: string; A: number; fullMark: number }[];
}

// For Recharts AreaChart
export interface DetectionsTimeline {

    data: { date: string; count: number }[];
}

// For Recharts Horizontal BarChart
export interface TopLocations {

    data: { name: string; count: number }[];
}

export interface LatencyHistory {

    data: { id: string; filename: string; latency: number; timestamp: string }[];
}

// Master Dashboard Payload
export interface DashboardResponse {

    summary: SummaryStats;
    severity: SeverityDistribution;
    surface: SurfaceDistribution;
    orientation: OrientationDistribution;
    timeline: DetectionsTimeline;
    top_locations: TopLocations;

}