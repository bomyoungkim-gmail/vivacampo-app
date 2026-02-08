import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { expect, userEvent, within } from '@storybook/test'
import { Bell, Sparkles } from 'lucide-react'
import { Button } from '../../base/Button'
import { DynamicIsland } from './DynamicIsland'

const meta = {
  title: 'Spatial/DynamicIsland',
  component: DynamicIsland,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof DynamicIsland>

export default meta

type Story = StoryObj<typeof meta>

export const Neutral: Story = {
  args: {
    title: 'Mapa sincronizado',
    description: 'Última atualização: agora',
    status: 'Online',
  },
}

export const Selection: Story = {
  args: {
    title: '2 talhões selecionados',
    description: 'Área total: 312 ha',
    variant: 'selection',
    status: 'Selecionado',
    actions: (
      <Button size="sm" variant="ghost">
        Detalhes
      </Button>
    ),
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    const button = canvas.getByRole('button', { name: /detalhes/i })
    await userEvent.click(button)
    await expect(button).toBeEnabled()
  },
}

export const Action: Story = {
  args: {
    title: 'Processando alertas',
    description: 'Gerando insights NDVI',
    variant: 'action',
    status: 'Em curso',
    ariaLive: 'assertive',
    actions: (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Sparkles className="h-4 w-4" />
        <span>12%</span>
        <Bell className="h-4 w-4" />
        <span>Notificar</span>
      </div>
    ),
  },
}
