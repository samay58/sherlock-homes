import { useState, useEffect, type FormEvent } from 'react'
import { useCriteria, useUpdateCriteria } from '@/hooks/useCriteria'
import type { Criteria } from '@/lib/types'
import './CriteriaPage.css'

const focusNeighborhoods = [
  'Dolores Heights',
  'Potrero Hill',
  'Cole Valley',
  'Haight-Ashbury',
  'NoPa',
]

const recencyOptions = [
  { value: 'fresh', label: 'Fresh' },
  { value: 'balanced', label: 'Balanced' },
  { value: 'hidden_gems', label: 'Hidden Gems' },
]

export function CriteriaPage() {
  const { data: criteria, isLoading: isLoadingCriteria, error: loadError } = useCriteria()
  const updateCriteria = useUpdateCriteria()

  const [formData, setFormData] = useState<Partial<Criteria>>({})
  const [avoidNeighborhoodsInput, setAvoidNeighborhoodsInput] = useState('')
  const [neighborhoodStrict, setNeighborhoodStrict] = useState(true)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    if (criteria) {
      setFormData({
        name: criteria.name ?? 'My Criteria',
        price_soft_max: criteria.price_soft_max ?? 3000000,
        price_max: criteria.price_max ?? 3500000,
        beds_min: criteria.beds_min ?? null,
        baths_min: criteria.baths_min ?? null,
        sqft_min: criteria.sqft_min ?? null,
        require_natural_light: criteria.require_natural_light ?? false,
        require_outdoor_space: criteria.require_outdoor_space ?? false,
        preferred_neighborhoods: criteria.preferred_neighborhoods ?? focusNeighborhoods,
        avoid_neighborhoods: criteria.avoid_neighborhoods ?? ['Pacific Heights'],
        neighborhood_mode: criteria.neighborhood_mode ?? 'strict',
        recency_mode: criteria.recency_mode ?? 'balanced',
        avoid_busy_streets: criteria.avoid_busy_streets ?? true,
      })
      setAvoidNeighborhoodsInput((criteria.avoid_neighborhoods || []).join(', '))
      setNeighborhoodStrict(criteria.neighborhood_mode === 'strict')
    }
  }, [criteria])

  const toggleNeighborhood = (name: string) => {
    const current = formData.preferred_neighborhoods ?? []
    if (current.includes(name)) {
      setFormData({ ...formData, preferred_neighborhoods: current.filter((item) => item !== name) })
    } else {
      setFormData({ ...formData, preferred_neighborhoods: [...current, name] })
    }
  }

  const parseAvoidNeighborhoods = (input: string): string[] => {
    return input
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length > 0)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSuccessMessage(null)

    const payload: Partial<Criteria> = {
      name: formData.name,
      price_max: formData.price_max || null,
      price_soft_max: formData.price_soft_max || null,
      beds_min: formData.beds_min || null,
      baths_min: formData.baths_min || null,
      sqft_min: formData.sqft_min || null,
      require_natural_light: formData.require_natural_light,
      require_outdoor_space: formData.require_outdoor_space,
      preferred_neighborhoods: formData.preferred_neighborhoods || [],
      avoid_neighborhoods: parseAvoidNeighborhoods(avoidNeighborhoodsInput),
      neighborhood_mode: neighborhoodStrict ? 'strict' : 'boost',
      recency_mode: formData.recency_mode || 'balanced',
      avoid_busy_streets: formData.avoid_busy_streets ?? true,
    }

    try {
      await updateCriteria.mutateAsync(payload)
      setSuccessMessage('Criteria saved successfully!')
    } catch {
      // Error is handled by the mutation
    }
  }

  if (isLoadingCriteria) {
    return (
      <section>
        <h2>My Matching Criteria</h2>
        <p>Loading criteria...</p>
      </section>
    )
  }

  const errorMessage = loadError?.message || updateCriteria.error?.message

  return (
    <section className="criteria-page">
      <h2>My Matching Criteria (Test User)</h2>

      {errorMessage && <p className="error">{errorMessage}</p>}
      {successMessage && <p className="success">{successMessage}</p>}

      {criteria && (
        <form onSubmit={handleSubmit} className="criteria-form">
          <div className="form-group">
            <label htmlFor="name">Criteria Name:</label>
            <input
              type="text"
              id="name"
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <fieldset>
            <legend>Budget</legend>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="price_soft_max">Soft Cap (preferred max):</label>
                <input
                  type="number"
                  id="price_soft_max"
                  value={formData.price_soft_max || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      price_soft_max: e.target.value ? Number(e.target.value) : null,
                    })
                  }
                  placeholder="3000000"
                />
              </div>
              <div className="form-group">
                <label htmlFor="price_max">Hard Cap (never exceed):</label>
                <input
                  type="number"
                  id="price_max"
                  value={formData.price_max || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      price_max: e.target.value ? Number(e.target.value) : null,
                    })
                  }
                  placeholder="3500000"
                />
              </div>
            </div>
          </fieldset>

          <fieldset>
            <legend>Neighborhood Focus</legend>
            <div className="neighborhood-grid">
              {focusNeighborhoods.map((neighborhood) => (
                <label key={neighborhood} className="checkbox-group neighborhood-option">
                  <input
                    type="checkbox"
                    checked={(formData.preferred_neighborhoods || []).includes(neighborhood)}
                    onChange={() => toggleNeighborhood(neighborhood)}
                  />
                  <span>{neighborhood}</span>
                </label>
              ))}
            </div>
            <div className="form-row">
              <div className="form-group checkbox-group">
                <input
                  type="checkbox"
                  id="neighborhood_strict"
                  checked={neighborhoodStrict}
                  onChange={(e) => setNeighborhoodStrict(e.target.checked)}
                />
                <label htmlFor="neighborhood_strict">Only show these neighborhoods</label>
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="avoid_neighborhoods">Avoid neighborhoods (optional):</label>
              <input
                type="text"
                id="avoid_neighborhoods"
                value={avoidNeighborhoodsInput}
                onChange={(e) => setAvoidNeighborhoodsInput(e.target.value)}
                placeholder="Pacific Heights"
              />
            </div>
          </fieldset>

          <fieldset>
            <legend>Recency</legend>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="recency_mode">Emphasis:</label>
                <select
                  id="recency_mode"
                  value={formData.recency_mode || 'balanced'}
                  onChange={(e) => setFormData({ ...formData, recency_mode: e.target.value })}
                >
                  {recencyOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </fieldset>

          <fieldset>
            <legend>Basics (Optional)</legend>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="beds_min">Min Beds:</label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  id="beds_min"
                  value={formData.beds_min || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      beds_min: e.target.value ? Number(e.target.value) : null,
                    })
                  }
                  placeholder="Any"
                />
              </div>
              <div className="form-group">
                <label htmlFor="baths_min">Min Baths:</label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  id="baths_min"
                  value={formData.baths_min || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      baths_min: e.target.value ? Number(e.target.value) : null,
                    })
                  }
                  placeholder="Any"
                />
              </div>
              <div className="form-group">
                <label htmlFor="sqft_min">Min Sqft:</label>
                <input
                  type="number"
                  step="50"
                  min="0"
                  id="sqft_min"
                  value={formData.sqft_min || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      sqft_min: e.target.value ? Number(e.target.value) : null,
                    })
                  }
                  placeholder="Any"
                />
              </div>
            </div>
          </fieldset>

          <fieldset>
            <legend>Qualities</legend>
            <div className="form-group checkbox-group">
              <input
                type="checkbox"
                id="natural_light"
                checked={formData.require_natural_light || false}
                onChange={(e) =>
                  setFormData({ ...formData, require_natural_light: e.target.checked })
                }
              />
              <label htmlFor="natural_light">Strong natural light</label>
            </div>
            <div className="form-group checkbox-group">
              <input
                type="checkbox"
                id="outdoor_space"
                checked={formData.require_outdoor_space || false}
                onChange={(e) =>
                  setFormData({ ...formData, require_outdoor_space: e.target.checked })
                }
              />
              <label htmlFor="outdoor_space">Outdoor space</label>
            </div>
            <div className="form-group checkbox-group">
              <input
                type="checkbox"
                id="quiet_streets"
                checked={formData.avoid_busy_streets || false}
                onChange={(e) => setFormData({ ...formData, avoid_busy_streets: e.target.checked })}
              />
              <label htmlFor="quiet_streets">Quiet streets</label>
            </div>
          </fieldset>

          <button type="submit" disabled={updateCriteria.isPending} aria-busy={updateCriteria.isPending}>
            {updateCriteria.isPending ? 'Saving...' : 'Save Criteria'}
          </button>
        </form>
      )}
    </section>
  )
}
