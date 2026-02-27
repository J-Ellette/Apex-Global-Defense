import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ClassificationBanner } from '../shared/components/ClassificationBanner'

describe('ClassificationBanner', () => {
  it('renders UNCLASSIFIED banner', () => {
    render(<ClassificationBanner level="UNCLASS" />)
    expect(screen.getByText('UNCLASSIFIED')).toBeInTheDocument()
  })

  it('renders SECRET banner', () => {
    render(<ClassificationBanner level="SECRET" />)
    expect(screen.getByText('SECRET')).toBeInTheDocument()
  })

  it('renders TS/SCI banner', () => {
    render(<ClassificationBanner level="TS_SCI" />)
    expect(screen.getByText('TOP SECRET // SCI')).toBeInTheDocument()
  })

  it('has correct aria-label for classification', () => {
    render(<ClassificationBanner level="FOUO" />)
    expect(
      screen.getByRole('banner', { name: /FOR OFFICIAL USE ONLY/i }),
    ).toBeInTheDocument()
  })

  it('handles numeric classification values from API payloads', () => {
    render(<ClassificationBanner level={4 as unknown as 'TS_SCI'} />)
    expect(screen.getByText('TOP SECRET // SCI')).toBeInTheDocument()
  })
})
