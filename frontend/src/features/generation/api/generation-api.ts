import { apiClient } from "@/lib/api-client";
import type { Job } from "@/types/api";

export type GenerationStage =
  | "research"
  | "script"
  | "scenes"
  | "image-prompts"
  | "images"
  | "voice"
  | "subtitles"
  | "video"
  | "thumbnail"
  | "seo";

export const generationApi = {
  async triggerStage(projectId: string, stage: GenerationStage): Promise<void> {
    await apiClient.post(`/projects/${projectId}/generate/${stage}`);
  },

  async triggerFullPipeline(projectId: string): Promise<void> {
    await apiClient.post(`/projects/${projectId}/generate/full-pipeline`);
  },

  async listJobs(projectId: string): Promise<Job[]> {
    const { data } = await apiClient.get<Job[]>(`/projects/${projectId}/generate/jobs`);
    return data;
  },
};
