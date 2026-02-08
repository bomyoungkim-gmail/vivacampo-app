import React from 'react'
import { render, screen } from '@testing-library/react'
import { Badge } from './Badge'

describe('Badge', () => {
  it('renders content', () => {
    render(<Badge>NDVI Alto</Badge>)
    expect(screen.getByText('NDVI Alto')).toBeInTheDocument()
  })
})
