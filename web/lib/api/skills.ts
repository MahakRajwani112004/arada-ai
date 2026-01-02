import { apiClient } from "./client";
import type {
  Skill,
  SkillListResponse,
  SkillSummary,
  SkillFile,
  CreateSkillRequest,
  UpdateSkillRequest,
  SkillFilters,
  GenerateSkillRequest,
  GenerateSkillResponse,
  RefineSkillRequest,
  RefineSkillResponse,
  SearchSkillsRequest,
  SearchSkillsResponse,
  RecommendSkillsRequest,
  RecommendSkillsResponse,
  TestSkillRequest,
  TestSkillResponse,
  PreviewSkillRequest,
  PreviewSkillResponse,
  SkillVersionsResponse,
  MarketplaceListResponse,
  PublishSkillRequest,
  PublishSkillResponse,
  ImportSkillRequest,
  ImportSkillResponse,
  RateSkillRequest,
  RateSkillResponse,
  SkillStats,
  SkillCategory,
  FileType,
} from "@/types/skill";

// ==================== Skill CRUD ====================

export async function listSkills(
  filters?: SkillFilters
): Promise<SkillListResponse> {
  const params = new URLSearchParams();
  if (filters?.category) params.append("category", filters.category);
  if (filters?.status) params.append("status", filters.status);
  if (filters?.search) params.append("search", filters.search);
  if (filters?.tags?.length) params.append("tags", filters.tags.join(","));
  if (filters?.include_public !== undefined)
    params.append("include_public", String(filters.include_public));

  const url = params.toString() ? `/skills?${params}` : "/skills";
  const response = await apiClient.get<SkillListResponse>(url);
  return response.data;
}

export async function getSkill(skillId: string): Promise<Skill> {
  const response = await apiClient.get<Skill>(`/skills/${skillId}`);
  return response.data;
}

export async function createSkill(request: CreateSkillRequest): Promise<Skill> {
  const response = await apiClient.post<Skill>("/skills", request);
  return response.data;
}

export async function updateSkill(
  skillId: string,
  request: UpdateSkillRequest
): Promise<Skill> {
  const response = await apiClient.put<Skill>(`/skills/${skillId}`, request);
  return response.data;
}

export async function deleteSkill(skillId: string): Promise<void> {
  await apiClient.delete(`/skills/${skillId}`);
}

// ==================== AI Generation ====================

export async function generateSkill(
  request: GenerateSkillRequest
): Promise<GenerateSkillResponse> {
  const response = await apiClient.post<GenerateSkillResponse>(
    "/skills/generate",
    request
  );
  return response.data;
}

export async function refineSkill(
  request: RefineSkillRequest
): Promise<RefineSkillResponse> {
  const response = await apiClient.post<RefineSkillResponse>(
    "/skills/generate/refine",
    request
  );
  return response.data;
}

// ==================== Search & Discovery ====================

export async function searchSkills(
  request: SearchSkillsRequest
): Promise<SearchSkillsResponse> {
  const response = await apiClient.post<SearchSkillsResponse>(
    "/skills/search",
    request
  );
  return response.data;
}

export async function recommendSkills(
  request: RecommendSkillsRequest
): Promise<RecommendSkillsResponse> {
  const response = await apiClient.post<RecommendSkillsResponse>(
    "/skills/recommendations",
    request
  );
  return response.data;
}

// ==================== Testing ====================

export async function testSkill(
  skillId: string,
  request: TestSkillRequest
): Promise<TestSkillResponse> {
  const response = await apiClient.post<TestSkillResponse>(
    `/skills/${skillId}/test`,
    request
  );
  return response.data;
}

export async function previewSkill(
  request: PreviewSkillRequest
): Promise<PreviewSkillResponse> {
  const response = await apiClient.post<PreviewSkillResponse>(
    "/skills/preview",
    request
  );
  return response.data;
}

// ==================== Versioning ====================

export async function getSkillVersions(
  skillId: string
): Promise<SkillVersionsResponse> {
  const response = await apiClient.get<SkillVersionsResponse>(
    `/skills/${skillId}/versions`
  );
  return response.data;
}

export async function rollbackSkillVersion(
  skillId: string,
  version: number
): Promise<Skill> {
  const response = await apiClient.post<Skill>(
    `/skills/${skillId}/versions/${version}/rollback`
  );
  return response.data;
}

// ==================== Marketplace ====================

export interface MarketplaceFilters {
  category?: SkillCategory;
  tags?: string[];
  search?: string;
  sort_by?: "popular" | "recent" | "rating";
  limit?: number;
  offset?: number;
}

export async function browseMarketplace(
  filters?: MarketplaceFilters
): Promise<MarketplaceListResponse> {
  const params = new URLSearchParams();
  if (filters?.category) params.append("category", filters.category);
  if (filters?.search) params.append("search", filters.search);
  if (filters?.tags?.length) params.append("tags", filters.tags.join(","));
  if (filters?.sort_by) params.append("sort_by", filters.sort_by);
  if (filters?.limit) params.append("limit", String(filters.limit));
  if (filters?.offset) params.append("offset", String(filters.offset));

  const url = params.toString()
    ? `/skills/marketplace?${params}`
    : "/skills/marketplace";
  const response = await apiClient.get<MarketplaceListResponse>(url);
  return response.data;
}

export async function publishSkill(
  skillId: string,
  request: PublishSkillRequest
): Promise<PublishSkillResponse> {
  const response = await apiClient.post<PublishSkillResponse>(
    `/skills/${skillId}/publish`,
    request
  );
  return response.data;
}

export async function importSkill(
  marketplaceId: string,
  request: ImportSkillRequest
): Promise<ImportSkillResponse> {
  const response = await apiClient.post<ImportSkillResponse>(
    `/skills/marketplace/${marketplaceId}/import`,
    request
  );
  return response.data;
}

export async function rateSkill(
  marketplaceId: string,
  request: RateSkillRequest
): Promise<RateSkillResponse> {
  const response = await apiClient.post<RateSkillResponse>(
    `/skills/marketplace/${marketplaceId}/rate`,
    request
  );
  return response.data;
}

// ==================== Stats ====================

export async function getSkillStats(skillId: string): Promise<SkillStats> {
  const response = await apiClient.get<SkillStats>(`/skills/${skillId}/stats`);
  return response.data;
}

// ==================== File Management ====================

export interface UploadFileResponse {
  file: SkillFile;
  message: string;
}

export interface SupportedFileTypesResponse {
  extensions: string[];
  max_size_mb: number;
}

export async function uploadSkillFile(
  skillId: string,
  file: File,
  fileType: FileType = "reference"
): Promise<UploadFileResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("file_type", fileType);

  const response = await apiClient.post<UploadFileResponse>(
    `/skills/${skillId}/files`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
}

export async function listSkillFiles(skillId: string): Promise<SkillFile[]> {
  const response = await apiClient.get<{ files: SkillFile[] }>(
    `/skills/${skillId}/files`
  );
  return response.data.files;
}

export async function getSkillFileDownloadUrl(
  skillId: string,
  fileId: string
): Promise<string> {
  const response = await apiClient.get<{ download_url: string; expires_at: string }>(
    `/skills/${skillId}/files/${fileId}/download`
  );
  return response.data.download_url;
}

export async function deleteSkillFile(
  skillId: string,
  fileId: string
): Promise<void> {
  await apiClient.delete(`/skills/${skillId}/files/${fileId}`);
}

export async function getSupportedFileTypes(): Promise<SupportedFileTypesResponse> {
  const response = await apiClient.get<SupportedFileTypesResponse>(
    "/skills/supported-file-types"
  );
  return response.data;
}

// ==================== Helper Functions ====================

/**
 * Get skills by category
 */
export async function getSkillsByCategory(
  category: SkillCategory
): Promise<SkillSummary[]> {
  const response = await listSkills({ category });
  return response.skills;
}

/**
 * Get public skills from marketplace
 */
export async function getPublicSkills(): Promise<SkillSummary[]> {
  const response = await listSkills({ include_public: true });
  return response.skills.filter((skill) => skill.is_public);
}

/**
 * Get user's draft skills
 */
export async function getDraftSkills(): Promise<SkillSummary[]> {
  const response = await listSkills({ status: "draft" });
  return response.skills;
}

/**
 * Quick search for skills (returns just names and IDs)
 */
export async function quickSearchSkills(
  query: string
): Promise<{ id: string; name: string }[]> {
  const response = await listSkills({ search: query });
  return response.skills.map((skill) => ({
    id: skill.id,
    name: skill.name,
  }));
}
