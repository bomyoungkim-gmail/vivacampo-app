import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { expect, userEvent, within } from '@storybook/test'
import axe from 'axe-core'
import { render, screen } from '@testing-library/react'
import { test } from 'vitest'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './Card'
import { Button } from '../Button'

const meta = {
  title: 'Base/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Card>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => (
    <Card className="w-[360px]">
      <CardHeader>
        <CardTitle>Resumo da Fazenda</CardTitle>
        <CardDescription>Última atualização: hoje</CardDescription>
      </CardHeader>
      <CardContent>
        NDVI médio: 0.62 · Alertas críticos: 2 · Área: 1.240 ha
      </CardContent>
      <CardFooter>
        <Button size="sm">Ver detalhes</Button>
        <Button variant="ghost" size="sm">Comparar</Button>
      </CardFooter>
    </Card>
  ),
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    await expect(canvas.getByText('Resumo da Fazenda')).toBeVisible()
    const detailsButton = canvas.getByRole('button', { name: 'Ver detalhes' })
    await userEvent.click(detailsButton)
    await expect(detailsButton).toBeEnabled()
    const a11yResults = await axe.run(canvasElement)
    await expect(a11yResults.violations).toEqual([])
  },
}

test('Card story interactions', async () => {
  render(
    <Card className="w-[360px]">
      <CardHeader>
        <CardTitle>Resumo da Fazenda</CardTitle>
        <CardDescription>Última atualização: hoje</CardDescription>
      </CardHeader>
      <CardContent>
        NDVI médio: 0.62 · Alertas críticos: 2 · Área: 1.240 ha
      </CardContent>
      <CardFooter>
        <Button size="sm">Ver detalhes</Button>
        <Button variant="ghost" size="sm">Comparar</Button>
      </CardFooter>
    </Card>
  )
  await expect(screen.getByText('Resumo da Fazenda')).toBeVisible()
  await expect(screen.getByRole('button', { name: 'Ver detalhes' })).toBeVisible()
})
