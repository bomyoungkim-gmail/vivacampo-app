import React from 'react'
import { render, screen } from '@testing-library/react'
import { Input } from './Input'

describe('Input', () => {
  it('renders with placeholder', () => {
    render(<Input placeholder="Nome da fazenda" />)
    expect(screen.getByPlaceholderText('Nome da fazenda')).toBeInTheDocument()
  })

  it('supports value', () => {
    render(<Input value="Fazenda Santa Maria" readOnly />)
    expect(screen.getByDisplayValue('Fazenda Santa Maria')).toBeInTheDocument()
  })
})
