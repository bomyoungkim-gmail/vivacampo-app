import type { Meta, StoryObj } from '@storybook/react'
import { expect, userEvent, within } from '@storybook/test'
import { CommandCenter, type CommandCenterItem } from './CommandCenter'

const items: CommandCenterItem[] = [
  { id: 'search-farms', label: 'Buscar fazenda', description: 'Abrir busca por fazenda', shortcut: 'F' },
  { id: 'new-aoi', label: 'Criar AOI', description: 'Desenhar uma nova área', shortcut: 'A' },
  { id: 'toggle-weather', label: 'Clima ao vivo', description: 'Alternar camada de clima', shortcut: 'C' },
  { id: 'open-analytics', label: 'Dashboard de insights', description: 'Abrir visão analítica', shortcut: 'I' },
]

const meta = {
  title: 'Spatial/CommandCenter',
  component: CommandCenter,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof CommandCenter>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    items,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)
    const trigger = canvas.getByRole('button')
    await userEvent.click(trigger)

    const input = canvas.getByPlaceholderText('Pesquisar comandos, lugares ou camadas…')
    await userEvent.type(input, 'faz')

    const option = canvas.getByRole('option', { name: /buscar fazenda/i })
    await expect(option).toBeVisible()
    await userEvent.keyboard('[ArrowDown]')
    await userEvent.keyboard('[Enter]')
    await expect(canvas.queryByRole('listbox')).not.toBeInTheDocument()
  },
}

export const Opened: Story = {
  args: {
    items,
    isOpen: true,
  },
}
