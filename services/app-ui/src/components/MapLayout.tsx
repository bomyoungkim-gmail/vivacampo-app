'use client'

import * as React from 'react'
import { cn } from '../lib/utils'

export type MapLayoutProps = {
  map: React.ReactNode
  topLeft?: React.ReactNode
  topCenter?: React.ReactNode
  topRight?: React.ReactNode
  bottomLeft?: React.ReactNode
  bottomCenter?: React.ReactNode
  bottomRight?: React.ReactNode
  children?: React.ReactNode
  className?: string
}

export default function MapLayout({
  map,
  topLeft,
  topCenter,
  topRight,
  bottomLeft,
  bottomCenter,
  bottomRight,
  children,
  className,
}: MapLayoutProps) {
  return (
    <div className={cn('relative h-full w-full', className)}>
      <div className="absolute inset-0 z-[var(--z-base)]">{map}</div>
      <div className="pointer-events-none absolute inset-0">
        {topLeft ? (
          <div className="pointer-events-auto absolute left-4 top-4 z-[var(--z-fixed)]">
            {topLeft}
          </div>
        ) : null}
        {topCenter ? (
          <div className="pointer-events-auto absolute left-1/2 top-4 z-[var(--z-fixed)] -translate-x-1/2">
            {topCenter}
          </div>
        ) : null}
        {topRight ? (
          <div className="pointer-events-auto absolute right-4 top-4 z-[var(--z-fixed)]">
            {topRight}
          </div>
        ) : null}
        {bottomLeft ? (
          <div className="pointer-events-auto absolute bottom-4 left-4 z-[var(--z-fixed)]">
            {bottomLeft}
          </div>
        ) : null}
        {bottomCenter ? (
          <div className="pointer-events-auto absolute bottom-6 left-1/2 z-[var(--z-fixed)] -translate-x-1/2">
            {bottomCenter}
          </div>
        ) : null}
        {bottomRight ? (
          <div className="pointer-events-auto absolute bottom-4 right-4 z-[var(--z-fixed)]">
            {bottomRight}
          </div>
        ) : null}
        {children ? (
          <div className="pointer-events-auto absolute inset-0 z-[var(--z-overlay)]">{children}</div>
        ) : null}
      </div>
    </div>
  )
}
