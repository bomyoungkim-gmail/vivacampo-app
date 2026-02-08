import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CommandCenter, type CommandCenterItem } from './CommandCenter'

describe('CommandCenter', () => {
  const items: CommandCenterItem[] = [
    { id: 'search-farms', label: 'Buscar fazenda' },
    { id: 'new-aoi', label: 'Criar AOI' },
  ]

  it('opens with keyboard shortcut and selects item', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()

    render(<CommandCenter items={items} onSelect={onSelect} />)

    await user.keyboard('{Meta>}k{/Meta}')
    const input = screen.getByPlaceholderText('Pesquisar comandos, lugares ou camadas…')
    await user.type(input, 'faz')
    await user.keyboard('{Enter}')

    expect(onSelect).toHaveBeenCalledWith(items[0])
  })

  it('navigates listbox with arrows', async () => {
    const user = userEvent.setup()
    render(<CommandCenter items={items} isOpen />)

    const input = screen.getByPlaceholderText('Pesquisar comandos, lugares ou camadas…')
    await user.click(input)
    await user.keyboard('{ArrowDown}')

    const option = screen.getByRole('option', { name: /criar aoi/i })
    expect(option).toHaveAttribute('aria-selected', 'true')
  })
})
