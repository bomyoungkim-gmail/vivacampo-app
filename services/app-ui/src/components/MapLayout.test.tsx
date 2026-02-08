import React from 'react'
import { render, screen } from '@testing-library/react'
import MapLayout from './MapLayout'

describe('MapLayout', () => {
  it('renders map and overlay slots', () => {
    render(
      <MapLayout
        map={<div>Mapa</div>}
        topLeft={<button type="button">Topo</button>}
        bottomRight={<div>Rodape</div>}
      >
        <div>Overlay</div>
      </MapLayout>
    )

    expect(screen.getByText('Mapa')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Topo' })).toBeInTheDocument()
    expect(screen.getByText('Rodape')).toBeInTheDocument()
    expect(screen.getByText('Overlay')).toBeInTheDocument()
  })
})
