import React from 'react'
import { render, screen } from '@testing-library/react'
import { DynamicIsland } from './DynamicIsland'

describe('DynamicIsland', () => {
  it('renders title, description and status', () => {
    render(
      <DynamicIsland
        title="Mapa sincronizado"
        description="Última atualização: agora"
        status="Online"
      />
    )

    expect(screen.getByText('Mapa sincronizado')).toBeInTheDocument()
    expect(screen.getByText('Última atualização: agora')).toBeInTheDocument()
    expect(screen.getByText('Online')).toBeInTheDocument()
  })

  it('sets aria-live status', () => {
    render(<DynamicIsland title="Status" />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite')
  })
})
