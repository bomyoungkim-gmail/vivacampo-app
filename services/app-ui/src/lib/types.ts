/**
 * Type Definitions for VivaCampo API
 *
 * This file contains all TypeScript interfaces and types for the application.
 * Eliminates the use of 'any' type and provides type safety.
 */

// =============================================================================
// Authentication & User Types
// =============================================================================

export interface User {
    id: string
    email: string
    name: string
    sub?: string
    picture?: string
}

export interface AuthResponse {
    access_token: string
    token_type: string
    identity: User
}

// =============================================================================
// Farm Types
// =============================================================================

export interface Farm {
    id: string
    name: string
    timezone: string
    aoi_count?: number
    created_at?: string
    updated_at?: string
}

export interface FarmCreateRequest {
    name: string
    timezone: string
}

export interface FarmListResponse {
    farms: Farm[]
    total: number
}

// =============================================================================
// AOI (Area of Interest) Types
// =============================================================================

export type AOIUseType = 'PASTURE' | 'CROP' | 'FOREST' | 'WATER' | 'OTHER'

export interface AOI {
    id: string
    farm_id: string
    name: string
    use_type: AOIUseType
    geometry: string  // WKT format
    area_ha?: number
    created_at?: string
    updated_at?: string
}

export interface AOICreateRequest {
    farm_id: string
    name: string
    use_type: AOIUseType
    geometry: string  // WKT format
}

export interface AOIUpdateRequest {
    name?: string
    use_type?: AOIUseType
    geometry?: string
}

export interface AOIBackfillRequest {
    aoi_id: string
    start_date: string  // ISO 8601 format
    end_date: string    // ISO 8601 format
}

// =============================================================================
// Signal Types
// =============================================================================

export type SignalType = 'CHANGE_DETECTED' | 'ANOMALY' | 'ALERT'
export type SignalStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED'

export interface Signal {
    id: string
    aoi_id: string
    aoi_name: string
    signal_type: SignalType
    status: SignalStatus
    score: number
    detected_at: string  // ISO 8601 format
    metadata?: Record<string, any>
    recommended_action?: string
    acknowledged_at?: string
    acknowledged_by?: string
    resolved_at?: string
    created_at?: string
    updated_at?: string
}

export interface SignalListParams {
    status?: SignalStatus
    signal_type?: SignalType
    aoi_id?: string
    limit?: number
    offset?: number
}

export interface SignalAcknowledgeRequest {
    notes?: string
}

export interface SignalFeedbackRequest {
    is_useful: boolean
    feedback_text?: string
}

// =============================================================================
// Job Types
// =============================================================================

export type JobStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
export type JobType = 'BACKFILL' | 'PROCESSING' | 'ANALYSIS' | 'OTHER'

export interface Job {
    id: string
    job_type: JobType
    status: JobStatus
    progress?: number  // 0-100
    aoi_id?: string
    aoi_name?: string
    started_at?: string
    completed_at?: string
    error_message?: string
    metadata?: Record<string, any>
    created_at?: string
    updated_at?: string
}

export interface JobListParams {
    status?: JobStatus
    job_type?: JobType
    limit?: number
    offset?: number
    aoi_id?: string
}

// =============================================================================
// AI Assistant Types
// =============================================================================

export type MessageRole = 'user' | 'assistant' | 'system'
export type ApprovalStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export interface AIThread {
    id: string
    signal_id?: string
    signal_info?: {
        aoi_name: string
        signal_type: SignalType
        score: number
    }
    created_at: string
    updated_at: string
}

export interface AIMessage {
    id: string
    thread_id: string
    role: MessageRole
    content: string
    metadata?: Record<string, any>
    created_at: string
}

export interface AIThreadCreateRequest {
    signal_id?: string | null
    initial_message: string
}

export interface AISendMessageRequest {
    message: string
}

export interface AIApproval {
    id: string
    thread_id: string
    action_type: string
    action_details: Record<string, any>
    status: ApprovalStatus
    created_at: string
    approved_at?: string
    rejected_at?: string
}

export interface AIApprovalDecisionRequest {
    approved: boolean
    notes?: string
}

// =============================================================================
// Chart & Visualization Types
// =============================================================================

export interface NDVIDataPoint {
    date: string  // ISO 8601 format
    value: number  // 0-1 range
    cloud_cover?: number
}

export interface TimeSeriesData {
    dates: string[]
    values: number[]
}

export interface ChartData {
    labels: string[]
    datasets: ChartDataset[]
}

export interface ChartDataset {
    label: string
    data: number[]
    borderColor?: string
    backgroundColor?: string
    fill?: boolean
}

// =============================================================================
// Map Types
// =============================================================================

export type Coordinate = [number, number]  // [latitude, longitude]

export interface MapBounds {
    north: number
    south: number
    east: number
    west: number
}

export interface WKTPolygon {
    coordinates: Coordinate[][]  // Array of polygons
}

// =============================================================================
// Derived Assets (Satellite Data)
// =============================================================================

export interface DerivedAssets {
    year: number
    week: number
    ndvi_s3_uri?: string | null
    anomaly_s3_uri?: string | null
    quicklook_s3_uri?: string | null
    ndwi_s3_uri?: string | null
    ndmi_s3_uri?: string | null
    savi_s3_uri?: string | null
    false_color_s3_uri?: string | null
    true_color_s3_uri?: string | null

    // Statistics
    ndvi_mean?: number
    ndvi_min?: number
    ndvi_max?: number
    ndvi_std?: number

    ndwi_mean?: number
    ndwi_min?: number
    ndwi_max?: number
    ndwi_std?: number

    ndmi_mean?: number
    ndmi_min?: number
    ndmi_max?: number
    ndmi_std?: number

    savi_mean?: number
    savi_min?: number
    savi_max?: number
    savi_std?: number

    anomaly_mean?: number
}

// =============================================================================
// API Response Types
// =============================================================================

export interface APIError {
    detail: string | ValidationError[]
    status_code: number
}

export interface ValidationError {
    loc: (string | number)[]
    msg: string
    type: string
}

export interface PaginatedResponse<T> {
    items: T[]
    total: number
    page: number
    page_size: number
    pages: number
}

export interface SuccessResponse {
    message: string
    data?: any
}

// =============================================================================
// Form Types
// =============================================================================

export interface LoginFormData {
    email: string
}

export interface FarmFormData {
    name: string
    timezone: string
}

export interface AOIFormData {
    name: string
    use_type: AOIUseType
    geometry: string
}

// =============================================================================
// Dashboard Types
// =============================================================================

export interface DashboardStats {
    farms: number
    activeSignals: number
    pendingJobs: number
}

export interface DashboardData {
    stats: DashboardStats
    recentSignals: Signal[]
    recentJobs: Job[]
}

// =============================================================================
// Admin Types (for admin-ui)
// =============================================================================

export interface Tenant {
    id: string
    name: string
    slug: string
    is_active: boolean
    created_at: string
    updated_at: string
}

export interface HealthCheck {
    status: 'healthy' | 'degraded' | 'unhealthy'
    version: string
    database: boolean
    redis?: boolean
    services: Record<string, boolean>
}

export interface AuditLog {
    id: string
    user_id?: string
    action: string
    resource_type: string
    resource_id?: string
    details?: Record<string, any>
    ip_address?: string
    user_agent?: string
    created_at: string
}

// =============================================================================
// Utility Types
// =============================================================================

// Make all properties optional
export type Partial<T> = {
    [P in keyof T]?: T[P]
}

// Make all properties required
export type Required<T> = {
    [P in keyof T]-?: T[P]
}

// Pick only specified properties
export type Pick<T, K extends keyof T> = {
    [P in K]: T[P]
}

// Omit specified properties
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>
