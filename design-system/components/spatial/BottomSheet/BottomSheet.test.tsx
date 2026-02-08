import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BottomSheet } from './BottomSheet'

describe('BottomSheet', () => {
  it('renders title and content when open', () => {
    render(
      <BottomSheet isOpen onClose={vi.fn()} title="Detalhes">
        <p>Conteudo</p>
      </BottomSheet>
    )

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Detalhes')).toBeInTheDocument()
    expect(screen.getByText('Conteudo')).toBeInTheDocument()
  })

  it('calls onClose when clicking close button', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()

    render(
      <BottomSheet isOpen onClose={onClose} title="Detalhes">
        <p>Conteudo</p>
      </BottomSheet>
    )

    await user.click(screen.getByRole('button', { name: /fechar/i }))
    expect(onClose).toHaveBeenCalled()
  })

  it('calls onClose on Escape', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()

    render(
      <BottomSheet isOpen onClose={onClose} title="Detalhes">
        <p>Conteudo</p>
      </BottomSheet>
    )

    await user.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalled()
  })
})
