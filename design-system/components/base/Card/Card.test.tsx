import React from 'react'
import { render, screen } from '@testing-library/react'
import { Card, CardHeader, CardTitle, CardContent } from './Card'

describe('Card', () => {
  it('renders content blocks', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Resumo</CardTitle>
        </CardHeader>
        <CardContent>Conteudo</CardContent>
      </Card>
    )
    expect(screen.getByText('Resumo')).toBeInTheDocument()
    expect(screen.getByText('Conteudo')).toBeInTheDocument()
  })
})
