import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { FieldDock, type FieldDockAction } from './FieldDock'

describe('FieldDock', () => {
  const actions: FieldDockAction[] = [
    { id: 'focus', label: 'Focar talhoes' },
    { id: 'measure', label: 'Medir area', active: true },
  ]

  it('renders actions and allows selection', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()
    const items = actions.map((action, index) =>
      index === 0 ? { ...action, onSelect } : action
    )

    render(<FieldDock actions={items} />)

    const button = screen.getByRole('button', { name: /focar talhoes/i })
    await user.click(button)

    expect(onSelect).toHaveBeenCalled()
  })

  it('marks active action as pressed', () => {
    render(<FieldDock actions={actions} />)

    const activeButton = screen.getByRole('button', { name: /medir area/i })
    expect(activeButton).toHaveAttribute('aria-pressed', 'true')
  })
})
