import { apiClient } from "@/lib/api-client";
import type { ContentTone, Project, ProjectDetail, ProjectListResponse } from "@/types/api";

export interface CreateProjectPayload {
  title: string;
  topic: string;
  tone: ContentTone;
  target_duration_seconds: number;
}

export const projectsApi = {
  async list(page = 1, pageSize = 12): Promise<ProjectListResponse> {
    const { data } = await apiClient.get<ProjectListResponse>("/projects", {
      params: { page, page_size: pageSize },
    });
    return data;
  },

  async get(projectId: string): Promise<ProjectDetail> {
    const { data } = await apiClient.get<ProjectDetail>(`/projects/${projectId}`);
    return data;
  },

  async create(payload: CreateProjectPayload): Promise<Project> {
    const { data } = await apiClient.post<Project>("/projects", payload);
    return data;
  },

  async remove(projectId: string): Promise<void> {
    await apiClient.delete(`/projects/${projectId}`);
  },
};
