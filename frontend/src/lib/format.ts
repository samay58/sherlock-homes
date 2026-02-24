import type { PropertyListing } from './types'

const PRICE_FORMATTER = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})
const NUMBER_FORMATTER = new Intl.NumberFormat('en-US')

export const formatPrice = (price: number | null) =>
  price == null ? 'Price TBD' : PRICE_FORMATTER.format(price)

export const formatNumber = (num: number | null) =>
  num == null ? '\u2014' : NUMBER_FORMATTER.format(num)

export const formatSqft = (sqft: number | null) => {
  if (sqft == null || sqft === 0) return 'N/A'
  return `${NUMBER_FORMATTER.format(sqft)} sqft`
}

export const formatScore = (score: number | null | undefined) => {
  if (score == null) return '\u2014'
  return `${Math.round(score)}%`
}

export const getScoreTier = (score: number) => {
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  if (score >= 40) return 'fair'
  return 'low'
}

const normalizeSignal = (value: unknown) => {
  if (value == null) return null
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return null
  return Math.round(numeric * 10) / 10
}

export function buildSignalData(listing: PropertyListing) {
  const data: { label: string; value: number }[] = []

  const deriveSignal = (key: string, fallback: number | null) => {
    if (listing.signals && (listing.signals as Record<string, unknown>)[key] != null) {
      return normalizeSignal((listing.signals as Record<string, unknown>)[key])
    }
    return normalizeSignal(fallback)
  }

  const light = deriveSignal(
    'light_potential',
    listing.light_potential_score != null ? listing.light_potential_score / 10 : null
  )
  const quiet = deriveSignal(
    'tranquility_score',
    listing.tranquility_score != null ? listing.tranquility_score / 10 : null
  )
  const visual = deriveSignal(
    'visual_quality',
    listing.visual_quality_score != null ? listing.visual_quality_score / 10 : null
  )
  const character = deriveSignal('nlp_character_score', null)

  if (light != null) data.push({ label: 'Light', value: light })
  if (quiet != null) data.push({ label: 'Quiet', value: quiet })
  if (visual != null) data.push({ label: 'Visual', value: visual })
  if (character != null) data.push({ label: 'Character', value: character })

  return data
}

export function buildFeatureTags(listing: PropertyListing) {
  return [
    listing.has_natural_light_keywords ? 'Natural Light' : null,
    listing.has_high_ceiling_keywords ? 'High Ceilings' : null,
    listing.has_outdoor_space_keywords ? 'Outdoor Space' : null,
    listing.has_parking_keywords ? 'Parking' : null,
    listing.has_view_keywords ? 'Views' : null,
    listing.has_updated_systems_keywords ? 'Updated Systems' : null,
    listing.has_architectural_details_keywords ? 'Character' : null,
  ].filter(Boolean) as string[]
}

export function getSourceLabel(source: string | null): string {
  if (!source) return 'Source'
  const map: Record<string, string> = {
    zillow: 'Zillow',
    streeteasy: 'StreetEasy',
    redfin: 'Redfin',
    trulia: 'Trulia',
    realtor: 'Realtor',
    craigslist: 'Craigslist',
  }
  return map[source.toLowerCase()] || source
}
