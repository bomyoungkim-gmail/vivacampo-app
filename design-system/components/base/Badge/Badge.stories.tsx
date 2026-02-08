import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { Badge } from './Badge'

const meta = {
  title: 'Base/Badge',
  component: Badge,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Badge>

export default meta

type Story = StoryObj<typeof meta>

export const Neutral: Story = {
  args: {
    variant: 'neutral',
    children: 'Neutro',
  },
}

export const Success: Story = {
  args: {
    variant: 'success',
    children: 'Saudavel',
  },
}

export const Warning: Story = {
  args: {
    variant: 'warning',
    children: 'Atencao',
  },
}

export const Critical: Story = {
  args: {
    variant: 'critical',
    children: 'Critico',
  },
}

export const Info: Story = {
  args: {
    variant: 'info',
    children: 'Info',
  },
}
