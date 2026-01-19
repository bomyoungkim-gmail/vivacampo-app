import { z } from 'zod'

// Farm validation schema
export const farmSchema = z.object({
    name: z.string().min(3, 'Nome deve ter pelo menos 3 caracteres').max(100, 'Nome muito longo'),
    timezone: z.string().min(1, 'Timezone é obrigatório'),
})

export type FarmFormData = z.infer<typeof farmSchema>

// AOI validation schema
export const aoiSchema = z.object({
    farm_id: z.string().uuid('ID da fazenda inválido'),
    name: z.string().min(3, 'Nome deve ter pelo menos 3 caracteres').max(100, 'Nome muito longo'),
    use_type: z.enum(['PASTURE', 'CROP', 'FOREST', 'OTHER'] as const, {
        message: 'Tipo de uso invalido',
    }),
    geometry: z.string().min(1, 'Geometria é obrigatória'),
})

export type AOIFormData = z.infer<typeof aoiSchema>

// Signal feedback schema
export const signalFeedbackSchema = z.object({
    feedback_type: z.enum(['CORRECT', 'FALSE_POSITIVE', 'NEEDS_REVIEW']),
    comment: z.string().max(500, 'Comentário muito longo').optional(),
})

export type SignalFeedbackData = z.infer<typeof signalFeedbackSchema>

// AI Assistant message schema
export const aiMessageSchema = z.object({
    content: z.string().min(1, 'Mensagem não pode estar vazia').max(2000, 'Mensagem muito longa'),
})

export type AIMessageData = z.infer<typeof aiMessageSchema>

// Login schema
export const loginSchema = z.object({
    email: z.string().email('Email inválido'),
})

export type LoginFormData = z.infer<typeof loginSchema>
