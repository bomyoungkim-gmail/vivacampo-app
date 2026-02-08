import { describe, expect, it } from 'vitest'
import { getZoomSemanticLevel } from './zoomSemantic'

describe('getZoomSemanticLevel', () => {
  it('returns macro for low zoom', () => {
    expect(getZoomSemanticLevel(6)).toBe('macro')
  })

  it('returns meso for mid zoom', () => {
    expect(getZoomSemanticLevel(10)).toBe('meso')
  })

  it('returns micro for high zoom', () => {
    expect(getZoomSemanticLevel(14)).toBe('micro')
  })
})
