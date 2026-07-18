import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { projectsApi, type CreateProjectPayload } from "@/features/projects/api/projects-api";
import { getApiErrorMessage } from "@/lib/api-client";
import type { ProjectStatus } from "@/types/api";

/** Statuses that mean "a background job is actively running" — poll faster while any project is in this state. */
function isAnyProjectActive(statuses: ProjectStatus[]): boolean {
  return statuses.some(
    (s) => s.startsWith("generating_") || s.startsWith("planning_") || s === "researching" || s === "scripting" || s === "rendering_video"
  );
}

export function useProjectsList(page = 1, pageSize = 12) {
  return useQuery({
    queryKey: ["projects", "list", page, pageSize],
    queryFn: () => projectsApi.list(page, pageSize),
    refetchInterval: (query) => {
      const statuses = query.state.data?.items.map((p) => p.status) ?? [];
      return isAnyProjectActive(statuses) ? 4_000 : false;
    },
  });
}

export function useProjectDetail(projectId: string | undefined) {
  return useQuery({
    queryKey: ["projects", "detail", projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: Boolean(projectId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status) return false;
      return isAnyProjectActive([status]) ? 3_000 : false;
    },
  });
}

export function useCreateProject() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateProjectPayload) => projectsApi.create(payload),
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ["projects", "list"] });
      toast.success("Project created — let's start generating.");
      navigate(`/projects/${project.id}`);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Couldn't create the project."));
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => projectsApi.remove(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", "list"] });
      toast.success("Project deleted.");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Couldn't delete the project."));
    },
  });
}
