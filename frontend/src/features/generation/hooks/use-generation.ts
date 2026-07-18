import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { generationApi, type GenerationStage } from "@/features/generation/api/generation-api";
import { getApiErrorMessage } from "@/lib/api-client";

const STAGE_LABELS: Record<GenerationStage, string> = {
  research: "Research",
  script: "Script",
  scenes: "Scene plan",
  "image-prompts": "Image prompts",
  images: "Images",
  voice: "Voice",
  subtitles: "Subtitles",
  video: "Video render",
  thumbnail: "Thumbnail",
  seo: "SEO metadata",
};

export function useProjectJobs(projectId: string | undefined) {
  return useQuery({
    queryKey: ["projects", "jobs", projectId],
    queryFn: () => generationApi.listJobs(projectId!),
    enabled: Boolean(projectId),
    refetchInterval: (query) => {
      const jobs = query.state.data ?? [];
      const anyRunning = jobs.some((j) => j.status === "pending" || j.status === "running");
      return anyRunning ? 2_500 : false;
    },
  });
}

export function useTriggerStage(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (stage: GenerationStage) => generationApi.triggerStage(projectId, stage),
    onSuccess: (_data, stage) => {
      toast.success(`${STAGE_LABELS[stage]} started.`);
      queryClient.invalidateQueries({ queryKey: ["projects", "detail", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects", "jobs", projectId] });
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Couldn't start that stage."));
    },
  });
}

export function useTriggerFullPipeline(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => generationApi.triggerFullPipeline(projectId),
    onSuccess: () => {
      toast.success("Full pipeline started — this will take a few minutes.");
      queryClient.invalidateQueries({ queryKey: ["projects", "detail", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects", "jobs", projectId] });
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Couldn't start the pipeline."));
    },
  });
}
