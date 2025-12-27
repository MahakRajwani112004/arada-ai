"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listSkills,
  getSkill,
  createSkill,
  updateSkill,
  deleteSkill,
  generateSkill,
  refineSkill,
  searchSkills,
  recommendSkills,
  testSkill,
  previewSkill,
  getSkillVersions,
  rollbackSkillVersion,
  browseMarketplace,
  publishSkill,
  importSkill,
  rateSkill,
  getSkillStats,
  uploadSkillFile,
  listSkillFiles,
  deleteSkillFile,
  getSupportedFileTypes,
} from "@/lib/api/skills";
import type { MarketplaceFilters } from "@/lib/api/skills";
import type {
  CreateSkillRequest,
  UpdateSkillRequest,
  SkillFilters,
  GenerateSkillRequest,
  RefineSkillRequest,
  SearchSkillsRequest,
  RecommendSkillsRequest,
  TestSkillRequest,
  PreviewSkillRequest,
  PublishSkillRequest,
  ImportSkillRequest,
  RateSkillRequest,
  FileType,
} from "@/types/skill";

// ==================== Query Keys ====================

export const skillKeys = {
  all: ["skills"] as const,
  lists: () => [...skillKeys.all, "list"] as const,
  list: (filters?: SkillFilters) => [...skillKeys.lists(), filters] as const,
  details: () => [...skillKeys.all, "detail"] as const,
  detail: (id: string) => [...skillKeys.details(), id] as const,
  versions: (id: string) => [...skillKeys.detail(id), "versions"] as const,
  stats: (id: string) => [...skillKeys.detail(id), "stats"] as const,
  files: (id: string) => [...skillKeys.detail(id), "files"] as const,
  supportedFileTypes: () => [...skillKeys.all, "supported-file-types"] as const,
  marketplace: (filters?: MarketplaceFilters) =>
    [...skillKeys.all, "marketplace", filters] as const,
};

// ==================== Skill CRUD Hooks ====================

export function useSkills(filters?: SkillFilters) {
  return useQuery({
    queryKey: skillKeys.list(filters),
    queryFn: () => listSkills(filters),
  });
}

export function useSkill(skillId: string) {
  return useQuery({
    queryKey: skillKeys.detail(skillId),
    queryFn: () => getSkill(skillId),
    enabled: !!skillId,
  });
}

export function useCreateSkill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateSkillRequest) => createSkill(request),
    onSuccess: (skill) => {
      queryClient.invalidateQueries({ queryKey: skillKeys.lists() });
      toast.success(`Skill "${skill.name}" created`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useUpdateSkill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      skillId,
      request,
    }: {
      skillId: string;
      request: UpdateSkillRequest;
    }) => updateSkill(skillId, request),
    onSuccess: (skill) => {
      queryClient.invalidateQueries({ queryKey: skillKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: skillKeys.detail(skill.id),
      });
      toast.success("Skill updated");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useDeleteSkill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (skillId: string) => deleteSkill(skillId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: skillKeys.lists() });
      toast.success("Skill deleted");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// ==================== AI Generation Hooks ====================

export function useGenerateSkill() {
  return useMutation({
    mutationFn: (request: GenerateSkillRequest) => generateSkill(request),
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useRefineSkill() {
  return useMutation({
    mutationFn: (request: RefineSkillRequest) => refineSkill(request),
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// ==================== Search & Discovery Hooks ====================

export function useSearchSkills() {
  return useMutation({
    mutationFn: (request: SearchSkillsRequest) => searchSkills(request),
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useRecommendSkills() {
  return useMutation({
    mutationFn: (request: RecommendSkillsRequest) => recommendSkills(request),
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// ==================== Testing Hooks ====================

export function useTestSkill() {
  return useMutation({
    mutationFn: ({
      skillId,
      request,
    }: {
      skillId: string;
      request: TestSkillRequest;
    }) => testSkill(skillId, request),
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function usePreviewSkill() {
  return useMutation({
    mutationFn: (request: PreviewSkillRequest) => previewSkill(request),
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// ==================== Versioning Hooks ====================

export function useSkillVersions(skillId: string) {
  return useQuery({
    queryKey: skillKeys.versions(skillId),
    queryFn: () => getSkillVersions(skillId),
    enabled: !!skillId,
  });
}

export function useRollbackSkillVersion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ skillId, version }: { skillId: string; version: number }) =>
      rollbackSkillVersion(skillId, version),
    onSuccess: (skill) => {
      queryClient.invalidateQueries({ queryKey: skillKeys.detail(skill.id) });
      queryClient.invalidateQueries({ queryKey: skillKeys.versions(skill.id) });
      toast.success(`Rolled back to version ${skill.version - 1}`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// ==================== Marketplace Hooks ====================

export function useMarketplace(filters?: MarketplaceFilters) {
  return useQuery({
    queryKey: skillKeys.marketplace(filters),
    queryFn: () => browseMarketplace(filters),
  });
}

export function usePublishSkill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      skillId,
      request,
    }: {
      skillId: string;
      request: PublishSkillRequest;
    }) => publishSkill(skillId, request),
    onSuccess: (response, { skillId }) => {
      queryClient.invalidateQueries({ queryKey: skillKeys.detail(skillId) });
      queryClient.invalidateQueries({ queryKey: skillKeys.lists() });
      toast.success("Skill published to marketplace");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useImportSkill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      marketplaceId,
      request,
    }: {
      marketplaceId: string;
      request: ImportSkillRequest;
    }) => importSkill(marketplaceId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: skillKeys.lists() });
      toast.success("Skill imported successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useRateSkill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      marketplaceId,
      request,
    }: {
      marketplaceId: string;
      request: RateSkillRequest;
    }) => rateSkill(marketplaceId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: skillKeys.marketplace() });
      toast.success("Rating submitted");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// ==================== Stats Hooks ====================

export function useSkillStats(skillId: string) {
  return useQuery({
    queryKey: skillKeys.stats(skillId),
    queryFn: () => getSkillStats(skillId),
    enabled: !!skillId,
  });
}

// ==================== File Management Hooks ====================

export function useSkillFiles(skillId: string) {
  return useQuery({
    queryKey: skillKeys.files(skillId),
    queryFn: () => listSkillFiles(skillId),
    enabled: !!skillId,
  });
}

export function useSupportedFileTypes() {
  return useQuery({
    queryKey: skillKeys.supportedFileTypes(),
    queryFn: () => getSupportedFileTypes(),
    staleTime: 1000 * 60 * 60, // Cache for 1 hour
  });
}

export function useUploadSkillFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      skillId,
      file,
      fileType,
    }: {
      skillId: string;
      file: File;
      fileType?: FileType;
    }) => uploadSkillFile(skillId, file, fileType),
    onSuccess: (response, { skillId }) => {
      queryClient.invalidateQueries({ queryKey: skillKeys.files(skillId) });
      queryClient.invalidateQueries({ queryKey: skillKeys.detail(skillId) });
      toast.success(`File "${response.file.name}" uploaded`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

export function useDeleteSkillFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ skillId, fileId }: { skillId: string; fileId: string }) =>
      deleteSkillFile(skillId, fileId),
    onSuccess: (_, { skillId }) => {
      queryClient.invalidateQueries({ queryKey: skillKeys.files(skillId) });
      queryClient.invalidateQueries({ queryKey: skillKeys.detail(skillId) });
      toast.success("File deleted");
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}
