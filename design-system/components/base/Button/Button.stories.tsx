import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { expect, userEvent, within } from '@storybook/test'
import axe from 'axe-core'
import { render, screen } from '@testing-library/react'
import { test } from 'vitest'
import { Button } from './Button'

const meta = {
  title: 'Base/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'ghost'],
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
  },
} satisfies Meta<typeof Button>

export default meta

type Story = StoryObj<typeof meta>

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Criar Alerta',
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    const button = canvas.getByRole('button', { name: 'Criar Alerta' })
    await expect(button).toBeVisible()
    await userEvent.tab()
    await expect(button).toHaveFocus()
    await userEvent.keyboard('[Enter]')
    const a11yResults = await axe.run(canvasElement)
    await expect(a11yResults.violations).toEqual([])
  },
}

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Cancelar',
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    const button = canvas.getByRole('button', { name: 'Cancelar' })
    await userEvent.click(button)
    await expect(button).toBeEnabled()
    const a11yResults = await axe.run(canvasElement)
    await expect(a11yResults.violations).toEqual([])
  },
}

export const Ghost: Story = {
  args: {
    variant: 'ghost',
    children: 'Ver detalhes',
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    const button = canvas.getByRole('button', { name: 'Ver detalhes' })
    await userEvent.click(button)
    await expect(button).toBeEnabled()
    const a11yResults = await axe.run(canvasElement)
    await expect(a11yResults.violations).toEqual([])
  },
}

test('Button story interactions', async () => {
  render(<Button variant="primary">Criar Alerta</Button>)
  const button = screen.getByRole('button', { name: 'Criar Alerta' })
  await userEvent.click(button)
  await expect(button).toBeEnabled()
})
