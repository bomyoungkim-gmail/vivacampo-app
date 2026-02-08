import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { expect, userEvent, within } from '@storybook/test'
import { Droplet, Layers, LocateFixed, MapPin, Ruler, Sparkles } from 'lucide-react'
import { FieldDock, type FieldDockAction } from './FieldDock'

const baseActions: FieldDockAction[] = [
  { id: 'focus', label: 'Focar talhões', icon: <LocateFixed className="h-4 w-4" /> },
  { id: 'measure', label: 'Medir área', icon: <Ruler className="h-4 w-4" /> },
  { id: 'layers', label: 'Camadas', icon: <Layers className="h-4 w-4" /> },
  { id: 'water', label: 'Irrigação', icon: <Droplet className="h-4 w-4" /> },
]

const meta = {
  title: 'Spatial/FieldDock',
  component: FieldDock,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof FieldDock>

export default meta

type Story = StoryObj<typeof meta>

export const Macro: Story = {
  args: {
    context: 'macro',
    actions: baseActions,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    const button = canvas.getByRole('button', { name: /focar talhoes/i })
    await userEvent.click(button)
    await expect(button).toBeEnabled()
  },
}

export const Meso: Story = {
  args: {
    context: 'meso',
    actions: baseActions.map((action) =>
      action.id === 'layers' ? { ...action, active: true } : action
    ),
  },
}

export const Micro: Story = {
  args: {
    context: 'micro',
    actions: [
      { id: 'pin', label: 'Fixar ponto', icon: <MapPin className="h-4 w-4" /> },
      { id: 'analysis', label: 'Analisar NDVI', icon: <Sparkles className="h-4 w-4" />, active: true },
      { id: 'water', label: 'Irrigação', icon: <Droplet className="h-4 w-4" />, disabled: true },
      { id: 'measure', label: 'Medir área', icon: <Ruler className="h-4 w-4" /> },
    ],
  },
}
