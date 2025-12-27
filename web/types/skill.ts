// Skill types - must match src/api/schemas/skills.py

// ==================== Enums ====================

export type SkillCategory =
  | "domain_expertise"
  | "document_generation"
  | "data_analysis"
  | "communication"
  | "research"
  | "coding"
  | "custom";

export type SkillStatus = "draft" | "published" | "archived";

export type FileType = "reference" | "template";

// ==================== Component Types ====================

export interface Terminology {
  id: string;
  term: string;
  definition: string;
  aliases?: string[];
}

export interface ReasoningPattern {
  id: string;
  name: string;
  steps: string[];
  description?: string;
}

export interface SkillExample {
  id: string;
  input: string;
  output: string;
  context?: string;
}

export interface SkillFile {
  id: string;
  name: string;
  file_type: FileType;
  mime_type: string;
  storage_url: string;
  content_preview: string;
  size_bytes: number;
  uploaded_at: string;
}

export interface CodeSnippet {
  id: string;
  language: string;
  code: string;
  description?: string;
}

export interface SkillResources {
  files: SkillFile[];
  code_snippets: CodeSnippet[];
}

export interface SkillParameter {
  id: string;
  name: string;
  type: "string" | "number" | "boolean" | "select";
  description?: string;
  required: boolean;
  default_value?: unknown;
  options?: string[]; // for select type
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
  };
}

export interface SkillExpertise {
  domain: string;
  terminology: Terminology[];
  reasoning_patterns: ReasoningPattern[];
  examples: SkillExample[];
}

export interface SkillCapability {
  expertise: SkillExpertise;
}

export interface SkillPrompts {
  system_enhancement: string;
  variables: string[];
}

export interface SkillMetadata {
  id: string;
  name: string;
  version: string;
  category: SkillCategory;
  tags: string[];
}

export interface SkillDefinition {
  metadata: SkillMetadata;
  capability: SkillCapability;
  resources: SkillResources;
  parameters: SkillParameter[];
  prompts: SkillPrompts;
}

// ==================== Skill CRUD ====================

export interface CreateSkillRequest {
  name: string;
  description: string;
  category: SkillCategory;
  tags: string[];
  definition: SkillDefinition;
}

export interface UpdateSkillRequest {
  name?: string;
  description?: string;
  category?: SkillCategory;
  tags?: string[];
  definition?: SkillDefinition;
  status?: SkillStatus;
  changelog?: string;
}

export interface Skill {
  id: string;
  tenant_id: string;
  name: string;
  description: string;
  category: SkillCategory;
  tags: string[];
  definition: SkillDefinition;
  version: number;
  status: SkillStatus;
  is_public: boolean;
  rating_avg?: number;
  rating_count: number;
  install_count: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface SkillSummary {
  id: string;
  name: string;
  description: string;
  category: SkillCategory;
  tags: string[];
  version: number;
  status: SkillStatus;
  is_public: boolean;
  rating_avg?: number;
  rating_count: number;
  created_at: string;
  updated_at: string;
}

export interface SkillListResponse {
  skills: SkillSummary[];
  total: number;
}

// ==================== AI Generation ====================

export interface GenerateSkillRequest {
  prompt: string;
  domain?: string;
  context?: string;
  include_examples?: boolean;
  include_terminology?: boolean;
}

export interface GenerateSkillResponse {
  skill: SkillDefinition;
  explanation: string;
  confidence: number;
  suggestions: string[];
  warnings: string[];
}

export interface RefineSkillRequest {
  skill: SkillDefinition;
  feedback: string;
  focus_areas?: string[];
}

export interface RefineSkillResponse {
  skill: SkillDefinition;
  changes_made: string[];
  explanation: string;
}

// ==================== Search & Discovery ====================

export interface SearchSkillsRequest {
  query: string;
  categories?: SkillCategory[];
  tags?: string[];
  include_public?: boolean;
  limit?: number;
}

export interface SkillMatch {
  skill: SkillSummary;
  relevance_score: number;
  match_reason: string;
}

export interface SearchSkillsResponse {
  matches: SkillMatch[];
  query_understanding: string;
}

export interface RecommendSkillsRequest {
  task_description: string;
  agent_context?: string;
  max_skills?: number;
}

export interface RecommendSkillsResponse {
  recommendations: SkillMatch[];
  reasoning: string;
}

// ==================== Testing ====================

export interface TestSkillRequest {
  input: string;
  parameters?: Record<string, unknown>;
}

export interface TestSkillResponse {
  enhanced_prompt: string;
  prompt_token_count: number;
  execution_time_ms: number;
  preview_sections: string[];
}

export interface PreviewSkillRequest {
  definition: SkillDefinition;
  input: string;
  parameters?: Record<string, unknown>;
}

export interface PreviewSkillResponse {
  enhanced_prompt: string;
  prompt_token_count: number;
  execution_time_ms: number;
}

// ==================== Versioning ====================

export interface SkillVersion {
  version: number;
  changelog: string;
  created_at: string;
}

export interface SkillVersionsResponse {
  versions: SkillVersion[];
  current_version: number;
}

export interface RollbackSkillRequest {
  version: number;
}

// ==================== Marketplace ====================

export interface MarketplaceSkill {
  id: string;
  marketplace_id: string;
  name: string;
  description: string;
  category: SkillCategory;
  tags: string[];
  version: number;
  rating_avg?: number;
  rating_count: number;
  install_count: number;
  author?: string;
  created_at: string;
  preview_available: boolean;
}

export interface MarketplaceListResponse {
  skills: MarketplaceSkill[];
  total: number;
  categories: string[];
  popular_tags: string[];
}

export interface PublishSkillRequest {
  make_public: boolean;
}

export interface PublishSkillResponse {
  marketplace_id: string;
  url?: string;
  status: string;
}

export interface ImportSkillRequest {
  marketplace_id: string;
  customize_name?: string;
}

export interface ImportSkillResponse {
  skill_id: string;
  original_marketplace_id: string;
  status: string;
}

export interface RateSkillRequest {
  rating: number;
  review?: string;
}

export interface RateSkillResponse {
  new_average: number;
  total_ratings: number;
}

// ==================== Stats ====================

export interface SkillStats {
  total_executions: number;
  success_rate: number;
  avg_duration_ms: number;
}

// ==================== Filters ====================

export interface SkillFilters {
  category?: SkillCategory;
  status?: SkillStatus;
  tags?: string[];
  search?: string;
  include_public?: boolean;
}

// ==================== Helper Types ====================

// Type aliases for common patterns
export type SkillDetail = Skill;

// Category display names
export const SKILL_CATEGORY_LABELS: Record<SkillCategory, string> = {
  domain_expertise: "Domain Expertise",
  document_generation: "Document Generation",
  data_analysis: "Data Analysis",
  communication: "Communication",
  research: "Research",
  coding: "Coding",
  custom: "Custom",
};

// Status display names
export const SKILL_STATUS_LABELS: Record<SkillStatus, string> = {
  draft: "Draft",
  published: "Published",
  archived: "Archived",
};

// Empty skill definition for creating new skills
export const createEmptySkillDefinition = (
  name: string = "",
  category: SkillCategory = "custom"
): SkillDefinition => ({
  metadata: {
    id: "",
    name,
    version: "1.0.0",
    category,
    tags: [],
  },
  capability: {
    expertise: {
      domain: "",
      terminology: [],
      reasoning_patterns: [],
      examples: [],
    },
  },
  resources: {
    files: [],
    code_snippets: [],
  },
  parameters: [],
  prompts: {
    system_enhancement: "",
    variables: [],
  },
});
