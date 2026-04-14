export type Severity = 'low' | 'medium' | 'high';
export type Orientation = 'vertical' | 'horizontal' | 'diagonal' | 'forked' | 'unknown';


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
    fractal_dimension?: number;
    severity: Severity;

}

export interface CrackInstance {

    crack_index: number;
    confidence: number;
    bbox: [number, number, number, number];
    mask_polygon: [number, number][];
    mask_area_px: number;
    max_width_px: number | null;
    max_length_px: number | null;
    orientation: Orientation | null;
    severity: Severity | null;
    fractal_dimension: number | null;

}
export interface DetectionDocument {

    id: string;     // carefull I change from _id -> id, it might trigger issues , I wil lse whant happens ...
    image_id: string;
    user_id: string;
    filename: string;
    surface_type: string;
    image_width: number;
    image_height: number;
    inference_ms: number;
    total_cracks: number;
    detections: CrackInstance[];
    detected_at: string; // ISO Date

}

export interface FractalChartData {

    area: number;
    fractalDim: number;
    severity: string;
    filename: string;

}
export interface PaginatedUsers {

    results: User[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;

}

export interface User {

    id: string;
    email: string;
    username: string;
    gender?: string | null;
    phone_number?: string | null;
    country?: string | null;
    is_admin: boolean;
    is_active: boolean;
    created_at: string;
    updated_at: string;

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
    stored_path?: string;
    mime_type?: string;
    size_bytes?: number;
    width_px?: number;
    height_px?: number;
    total_cracks_detected: number;
    inference_status: InferenceStatus;
    inference_ms?: number;
    uploaded_at: string;
    updated_at?: string;
    // URLs generadas por el backend
    raw_url?: string;
    output_url?: string;

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
    deleted_id: string;
    deleted_at: string;
}

export interface PaginatedImages {

    results: ImageDoc[];
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

export interface LocationFullUpdate extends LocationCreate { }

export type LocationPatchUpdate = Partial<LocationCreate>;

export interface PaginatedLocations {

    results: Location[];
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
    surface_types: string[];

}

export interface PaginatedDetections {

    results: DetectionDocument[];
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

    total_images_analyzed: number;
    total_cracks_detected: number;
    average_confidence: number;
    average_inference_ms: number;
    most_cracked_image: {
        image_id: string;
        filename: string;
        total_cracks: number;
        uploaded_at: string;
    } | null;

}

export interface SeveritySlice {
    name: string;
    value: number;
    fill: string;
}

export interface SeverityDistribution {

    data: SeveritySlice[];
    total_instances: number;
}

export interface SurfaceBar {
    surface: string;
    cracks: number;
    images: number;
}

export interface SurfaceDistribution {

    data: SurfaceBar[];
}

export interface OrientationPoint {
    orientation: string;
    count: number;
}

export interface OrientationDistribution {

    data: OrientationPoint[];
}

export interface AnalyticsTimelinePoint {
    date: string;
    total_cracks: number;
    total_images: number;
}

export interface DetectionsTimeline {

    data: AnalyticsTimelinePoint[];
    period_days: number;
}

export interface TopLocation {
    location_id: string;
    name: string;
    city: string;
    total_cracks: number;
    total_images: number;
}

export interface TopLocations {

    data: TopLocation[];
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
    locations: TopLocations;

}
