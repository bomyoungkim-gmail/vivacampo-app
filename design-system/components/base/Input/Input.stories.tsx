import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { expect, userEvent, within } from '@storybook/test'
import axe from 'axe-core'
import { render, screen } from '@testing-library/react'
import { test } from 'vitest'
import { Input } from './Input'

const meta = {
  title: 'Base/Input',
  component: Input,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Input>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    placeholder: 'Digite o nome da fazenda',
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    const input = canvas.getByPlaceholderText('Digite o nome da fazenda')
    await userEvent.type(input, 'Fazenda Aurora')
    await expect(input).toHaveValue('Fazenda Aurora')
    await userEvent.clear(input)
    await expect(input).toHaveValue('')
    await userEvent.tab()
    await expect(input).toHaveFocus()
    const a11yResults = await axe.run(canvasElement)
    await expect(a11yResults.violations).toEqual([])
  },
}

export const WithValue: Story = {
  args: {
    value: 'Fazenda Santa Maria',
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    await expect(canvas.getByDisplayValue('Fazenda Santa Maria')).toBeVisible()
    const a11yResults = await axe.run(canvasElement)
    await expect(a11yResults.violations).toEqual([])
  },
}

test('Input story interactions', async () => {
  render(<Input placeholder="Digite o nome da fazenda" />)
  const input = screen.getByPlaceholderText('Digite o nome da fazenda')
  await userEvent.type(input, 'Fazenda Aurora')
  await expect(input).toHaveValue('Fazenda Aurora')
})
