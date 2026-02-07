import axios, { AxiosResponse } from 'axios'
import { APP_CONFIG } from './config'
import type {
    Farm,
    FarmCreateRequest,
    AOI,
    AOICreateRequest,
    AOIUpdateRequest,
    AOIBackfillRequest,
    Signal,
    SignalListParams,
    SignalAcknowledgeRequest,
    SignalFeedbackRequest,
    Job,
    JobListParams,
    AIThread,
    AIMessage,
    AIThreadCreateRequest,
    AISendMessageRequest,
    AIApproval,
    AIApprovalDecisionRequest,
    DerivedAssets,
    RadarAssets,
    RawDerivedAssets,
    RawRadarAssets,
    WeatherData,
    AoiSplitSimulationRequest,
    AoiSplitSimulationResponse,
    AoiSplitCreateRequest,
    AoiSplitCreateResponse,
    AoiStatusRequest,
    AoiStatusResponse,
    FieldCalibrationCreateRequest,
    FieldCalibrationCreateResponse,
    PredictionResponse,
    InviteMemberRequest,
    InviteMemberResponse,
    Membership,
} from './types'

const api = axios.create({
    baseURL: APP_CONFIG.API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

import useUserStore from '@/stores/useUserStore'

// Add auth token to requests
api.interceptors.request.use((config) => {
    // Get token directly from Zustand store state (works outside components)
    const token = useUserStore.getState().token

    if (token) {
        // console.log('[API Interceptor] Attaching Token:', token.substring(0, 10) + '...')
        config.headers.Authorization = `Bearer ${token}`
    } else {
        console.warn('[API Interceptor] No token found in store')
    }
    return config
})

// Handle auth errors
let isRedirecting = false;

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Prevent infinite loops if already on login page
            if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
                if (!isRedirecting) {
                    isRedirecting = true;
                    // proper clean up via store action
                    useUserStore.getState().actions.logout();

                    // Force redirect to login
                    window.location.href = `${APP_CONFIG.BASE_PATH}/login`;
                }
            }
        }
        return Promise.reject(error)
    }
)

export default api

// =============================================================================
// Farm API
// =============================================================================

export const farmAPI = {
    list: (): Promise<AxiosResponse<Farm[]>> =>
        api.get('/v1/app/farms'),

    create: (data: FarmCreateRequest): Promise<AxiosResponse<Farm>> =>
        api.post('/v1/app/farms', data),

    delete: (id: string): Promise<AxiosResponse<void>> =>
        api.delete(`/v1/app/farms/${id}`),
}

// =============================================================================
// AOI API
// =============================================================================

export const aoiAPI = {
    list: (): Promise<AxiosResponse<AOI[]>> =>
        api.get('/v1/app/aois'),

    create: (data: AOICreateRequest): Promise<AxiosResponse<AOI>> =>
        api.post('/v1/app/aois', data),

    delete: (id: string): Promise<AxiosResponse<void>> =>
        api.delete(`/v1/app/aois/${id}`),

    update: (id: string, data: AOIUpdateRequest): Promise<AxiosResponse<AOI>> =>
        api.patch(`/v1/app/aois/${id}`, data),

    backfill: (id: string, data: AOIBackfillRequest): Promise<AxiosResponse<void>> =>
        api.post(`/v1/app/aois/${id}/backfill`, data),

    getAssets: async (id: string): Promise<AxiosResponse<DerivedAssets>> => {
        const response = await api.get<RawDerivedAssets>(`/v1/app/aois/${id}/assets`)
        const data = response.data
        const mapped: DerivedAssets = {
            ...data,
            ndvi_tile_url: data.ndvi_s3_uri ?? null,
            anomaly_tile_url: data.anomaly_s3_uri ?? null,
            quicklook_tile_url: data.quicklook_s3_uri ?? null,
            ndwi_tile_url: data.ndwi_s3_uri ?? null,
            ndmi_tile_url: data.ndmi_s3_uri ?? null,
            savi_tile_url: data.savi_s3_uri ?? null,
            false_color_tile_url: data.false_color_s3_uri ?? null,
            true_color_tile_url: data.true_color_s3_uri ?? null,
            ndre_tile_url: data.ndre_s3_uri ?? null,
            reci_tile_url: data.reci_s3_uri ?? null,
            gndvi_tile_url: data.gndvi_s3_uri ?? null,
            evi_tile_url: data.evi_s3_uri ?? null,
            msi_tile_url: data.msi_s3_uri ?? null,
            nbr_tile_url: data.nbr_s3_uri ?? null,
            bsi_tile_url: data.bsi_s3_uri ?? null,
            ari_tile_url: data.ari_s3_uri ?? null,
            cri_tile_url: data.cri_s3_uri ?? null,
        }
        return {
            ...response,
            data: mapped,
        }
    },

    getHistory: (id: string): Promise<AxiosResponse<DerivedAssets[]>> =>
        api.get(`/v1/app/aois/${id}/history`),

    listByFarm: (farmId: string): Promise<AxiosResponse<AOI[]>> =>
        api.get('/v1/app/aois', { params: { farm_id: farmId } }),

    getRadarHistory: async (id: string, year?: number): Promise<AxiosResponse<RadarAssets[]>> => {
        const response = await api.get<RawRadarAssets[]>(
            `/v1/app/aois/${id}/radar/history`,
            { params: { year } }
        )
        const mapped = response.data.map((row) => ({
            ...row,
            rvi_tile_url: row.rvi_s3_uri ?? null,
            ratio_tile_url: row.ratio_s3_uri ?? null,
            vv_tile_url: row.vv_s3_uri ?? null,
            vh_tile_url: row.vh_s3_uri ?? null,
        }))
        return {
            ...response,
            data: mapped,
        }
    },

    getWeatherHistory: (id: string, start?: string, end?: string): Promise<AxiosResponse<WeatherData[]>> =>
        api.get(`/v1/app/aois/${id}/weather/history`, { params: { start_date: start, end_date: end } }),

    getNitrogenStatus: (id: string) =>
        api.get(`/v1/app/aois/${id}/nitrogen/status`),

    simulateSplit: (data: AoiSplitSimulationRequest): Promise<AxiosResponse<AoiSplitSimulationResponse>> =>
        api.post('/v1/app/aois/simulate-split', data),

    splitAois: (data: AoiSplitCreateRequest): Promise<AxiosResponse<AoiSplitCreateResponse>> =>
        api.post('/v1/app/aois/split', data),

    getStatus: (data: AoiStatusRequest): Promise<AxiosResponse<AoiStatusResponse>> =>
        api.post('/v1/app/aois/status', data),
}

// =============================================================================
// Signal API
// =============================================================================

export const signalAPI = {
    list: (params?: SignalListParams): Promise<AxiosResponse<Signal[]>> =>
        api.get('/v1/app/signals', { params }),

    get: (id: string): Promise<AxiosResponse<Signal>> =>
        api.get(`/v1/app/signals/${id}`),

    acknowledge: (id: string, data?: SignalAcknowledgeRequest): Promise<AxiosResponse<Signal>> =>
        api.post(`/v1/app/signals/${id}/ack`, data),

    feedback: (id: string, data: SignalFeedbackRequest): Promise<AxiosResponse<void>> =>
        api.post(`/v1/app/signals/${id}/feedback`, data),

    listByFarm: (farmId: string): Promise<AxiosResponse<Signal[]>> =>
        api.get('/v1/app/signals', { params: { farm_id: farmId } }),
}

// =============================================================================
// Job API
// =============================================================================

export const jobAPI = {
    list: (params?: JobListParams): Promise<AxiosResponse<Job[]>> =>
        api.get('/v1/app/jobs', { params }),

    get: (id: string): Promise<AxiosResponse<Job>> =>
        api.get(`/v1/app/jobs/${id}`),

    retry: (id: string): Promise<AxiosResponse<Job>> =>
        api.post(`/v1/app/jobs/${id}/retry`),

    cancel: (id: string): Promise<AxiosResponse<Job>> =>
        api.post(`/v1/app/jobs/${id}/cancel`),
}

// =============================================================================
// Analytics API
// =============================================================================

export const analyticsAPI = {
    createFieldCalibration: (data: FieldCalibrationCreateRequest): Promise<AxiosResponse<FieldCalibrationCreateResponse>> =>
        api.post('/v1/app/field-data', data),

    getPrediction: (aoiId: string, metricType: 'biomass' | 'yield'): Promise<AxiosResponse<PredictionResponse>> =>
        api.get('/v1/app/analytics/prediction', { params: { aoi_id: aoiId, metric_type: metricType } }),
}

// =============================================================================
// AI Assistant API
// =============================================================================

export const aiAssistantAPI = {
    createThread: (data: AIThreadCreateRequest): Promise<AxiosResponse<AIThread>> =>
        api.post('/v1/app/ai-assistant/threads', data),

    listThreads: (): Promise<AxiosResponse<AIThread[]>> =>
        api.get('/v1/app/ai-assistant/threads'),

    sendMessage: (threadId: string, data: AISendMessageRequest): Promise<AxiosResponse<AIMessage>> =>
        api.post(`/v1/app/ai-assistant/threads/${threadId}/messages`, data),

    getMessages: (threadId: string): Promise<AxiosResponse<AIMessage[]>> =>
        api.get(`/v1/app/ai-assistant/threads/${threadId}/messages`),

    listApprovals: (): Promise<AxiosResponse<AIApproval[]>> =>
        api.get('/v1/app/ai-assistant/approvals'),

    decide: (approvalId: string, data: AIApprovalDecisionRequest): Promise<AxiosResponse<AIApproval>> =>
        api.post(`/v1/app/ai-assistant/approvals/${approvalId}/decide`, data),
}

// =============================================================================
// Tenant Admin API
// =============================================================================

export const tenantAdminAPI = {
    listMembers: (): Promise<AxiosResponse<Membership[]>> =>
        api.get('/v1/admin/tenant/members'),

    inviteMember: (data: InviteMemberRequest): Promise<AxiosResponse<InviteMemberResponse>> =>
        api.post('/v1/admin/tenant/members/invite', data),
}
