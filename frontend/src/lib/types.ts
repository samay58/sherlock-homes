// Type definitions based on backend schemas

export interface PropertyListing {
  id: number;
  address: string;
  price: number | null;
  beds: number | null;
  baths: number | null;
  sqft: number | null;
  property_type: string | null;
  url: string | null;
  listing_id: string | null;
  lat: number | null;
  lon: number | null;
  year_built: number | null;
  listing_status: string | null;
  description: string | null;
  neighborhood: string | null;
  days_on_market: number | null;

  // Feature flags (from NLP analysis)
  has_natural_light_keywords: boolean;
  has_high_ceiling_keywords: boolean;
  has_outdoor_space_keywords: boolean;
  has_parking_keywords: boolean;
  has_view_keywords: boolean;
  has_updated_systems_keywords: boolean;
  has_home_office_keywords: boolean;
  has_storage_keywords: boolean;
  has_open_floor_plan_keywords: boolean;
  has_architectural_details_keywords: boolean;
  has_luxury_keywords: boolean;
  has_designer_keywords: boolean;
  has_tech_ready_keywords: boolean;

  // Deal indicators
  is_price_reduced: boolean;
  is_back_on_market: boolean;

  // Red flags
  has_busy_street_keywords: boolean;
  is_north_facing_only: boolean;
  is_basement_unit: boolean;

  // Scores
  walk_score: number | null;
  transit_score: number | null;

  // Sherlock Homes Intelligence
  tranquility_score: number | null;  // 0-100, from geospatial
  tranquility_factors: Record<string, any> | null;
  light_potential_score: number | null;  // 0-100, from NLP
  light_potential_signals: string[] | null;

  // Visual Quality Intelligence (from Claude Vision photo analysis)
  visual_quality_score: number | null;  // 0-100, overall visual appeal
  visual_assessment: Record<string, any> | null;  // {modernity, condition, brightness, staging, cleanliness, red_flags, highlights}
  photos_hash: string | null;
  visual_analyzed_at: string | null;

  // Match data
  match_score?: number | null;
  match_narrative?: string | null;
  feature_scores?: Record<string, any> | null;
  match_reasons?: string[] | null;
  match_tradeoff?: string | null;

  photos: string[] | null;
  last_updated: string | null;
}

export interface Criteria {
    id: number;
    user_id: number;
    name: string | null;
    is_active: boolean | null;
    price_min: number | null;
    price_max: number | null;
    price_soft_max?: number | null;
    beds_min: number | null;
    baths_min: number | null;
    sqft_min: number | null;
    require_natural_light: boolean | null;
    require_high_ceilings: boolean | null;
    require_outdoor_space: boolean | null;
    preferred_neighborhoods?: string[] | null;
    avoid_neighborhoods?: string[] | null;
    neighborhood_mode?: string | null;
    max_days_on_market?: number | null;
    recency_mode?: string | null;
    avoid_busy_streets?: boolean | null;
}

// Add other types as needed (e.g., User, Auth responses) 
