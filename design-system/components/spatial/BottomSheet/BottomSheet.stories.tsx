import type { Meta, StoryObj } from '@storybook/react'
import React from 'react'
import { BottomSheet, type BottomSheetLevel } from './BottomSheet'

const meta = {
  title: 'Spatial/BottomSheet',
  component: BottomSheet,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof BottomSheet>

export default meta

type Story = StoryObj<typeof meta>

const DemoContent = () => (
  <div className="space-y-3 text-sm text-muted-foreground">
    <p>Resumo do talhao: 12,4 ha com vigor acima da media.</p>
    <div className="rounded-2xl border border-border/40 bg-background/70 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Insights</p>
      <p className="mt-2 text-foreground">
        Ultima analise detectou queda de NDVI e recomendou inspecao de pragas.
      </p>
    </div>
    <div className="rounded-2xl border border-border/40 bg-background/70 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Clima</p>
      <p className="mt-2 text-foreground">Chuva acumulada na semana: 18mm.</p>
    </div>
  </div>
)

const SheetStory = ({ level }: { level: BottomSheetLevel }) => {
  const [open, setOpen] = React.useState(true)

  return (
    <div className="min-h-screen bg-muted/40">
      <BottomSheet
        isOpen={open}
        onClose={() => setOpen(false)}
        initialLevel={level}
        title="Detalhes do Talhao"
      >
        <DemoContent />
      </BottomSheet>
      {!open && (
        <div className="flex min-h-screen items-center justify-center">
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="rounded-full border border-border/50 bg-background px-5 py-3 text-sm font-medium"
          >
            Reabrir sheet
          </button>
        </div>
      )}
    </div>
  )
}

export const Peek: Story = {
  render: () => <SheetStory level="peek" />,
}

export const Half: Story = {
  render: () => <SheetStory level="half" />,
}

export const Full: Story = {
  render: () => <SheetStory level="full" />,
}

export const Gestures: Story = {
  render: () => <SheetStory level="half" />,
}
