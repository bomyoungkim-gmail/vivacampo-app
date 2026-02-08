import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { Button } from '../Button'
import { TooltipContent, TooltipProvider, TooltipRoot, TooltipTrigger } from './Tooltip'

const meta = {
  title: 'Base/Tooltip',
  component: TooltipRoot,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof TooltipRoot>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => (
    <TooltipProvider>
      <TooltipRoot>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="sm">Detalhes</Button>
        </TooltipTrigger>
        <TooltipContent>Ver informacoes</TooltipContent>
      </TooltipRoot>
    </TooltipProvider>
  ),
}
