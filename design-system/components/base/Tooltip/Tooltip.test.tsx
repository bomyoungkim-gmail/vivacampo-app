import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TooltipContent, TooltipProvider, TooltipRoot, TooltipTrigger } from './Tooltip'

describe('Tooltip', () => {
  it('shows content on hover', async () => {
    const user = userEvent.setup()
    render(
      <TooltipProvider>
        <TooltipRoot>
          <TooltipTrigger asChild>
            <button type="button">Hover me</button>
          </TooltipTrigger>
          <TooltipContent>Conteudo</TooltipContent>
        </TooltipRoot>
      </TooltipProvider>
    )

    await user.hover(screen.getByRole('button', { name: 'Hover me' }))
    const matches = await screen.findAllByText('Conteudo')
    expect(matches.length).toBeGreaterThan(0)
  })
})
