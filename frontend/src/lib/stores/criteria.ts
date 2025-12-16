import { writable } from 'svelte/store';

export interface CriteriaValues {
  beds_min?: number;
  beds_max?: number;
  baths_min?: number;
  baths_max?: number;
  sqft_min?: number;
  sqft_max?: number;

  natural_light?: number; // 1-5 weight
  high_ceilings?: number;
  outdoor_space?: number;
  open_plan?: number;
  modern_interior?: number;
  walk_score?: number;
  garage?: number;
}

export const criteriaValues = writable<CriteriaValues>({ beds_min: 2, natural_light: 3 });
export const criteriaSetId = writable<number | null>(null); 