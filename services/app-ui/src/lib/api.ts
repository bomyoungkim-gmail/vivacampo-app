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

    getAssets: (id: string): Promise<AxiosResponse<DerivedAssets>> =>
        api.get(`/v1/app/aois/${id}/assets`),

    getHistory: (id: string): Promise<AxiosResponse<DerivedAssets[]>> =>
        api.get(`/v1/app/aois/${id}/history`),

    listByFarm: (farmId: string): Promise<AxiosResponse<AOI[]>> =>
        api.get('/v1/app/aois', { params: { farm_id: farmId } }),
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
