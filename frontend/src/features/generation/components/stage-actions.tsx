import { Button } from "@/components/ui/button";
import type { GenerationStage } from "@/features/generation/api/generation-api";
import { useTriggerFullPipeline, useTriggerStage } from "@/features/generation/hooks/use-generation";
import type { ProjectStatus } from "@/types/api";
import { Loader2, Sparkles } from "lucide-react";

const STAGE_SEQUENCE: { stage: GenerationStage; label: string; readyAfter: ProjectStatus | null }[] = [
  { stage: "research", label: "Run research", readyAfter: null },
  { stage: "script", label: "Write script", readyAfter: "research_ready" },
  { stage: "scenes", label: "Plan scenes", readyAfter: "script_ready" },
  { stage: "image-prompts", label: "Generate image prompts", readyAfter: "scenes_ready" },
  { stage: "images", label: "Generate images", readyAfter: "image_prompts_ready" },
  { stage: "voice", label: "Generate voice", readyAfter: "script_ready" },
  { stage: "subtitles", label: "Generate subtitles", readyAfter: "voice_ready" },
  { stage: "video", label: "Render video", readyAfter: "subtitles_ready" },
  { stage: "thumbnail", label: "Generate thumbnail", readyAfter: "video_ready" },
  { stage: "seo", label: "Generate SEO metadata", readyAfter: "script_ready" },
];

const STATUS_RANK: Record<ProjectStatus, number> = {
  draft: 0,
  researching: 1,
  research_ready: 2,
  scripting: 3,
  script_ready: 4,
  planning_scenes: 5,
  scenes_ready: 6,
  generating_image_prompts: 7,
  image_prompts_ready: 8,
  seo_ready: 9,
  generating_images: 10,
  images_ready: 11,
  generating_voice: 12,
  voice_ready: 13,
  generating_subtitles: 14,
  subtitles_ready: 15,
  rendering_video: 16,
  video_ready: 17,
  generating_thumbnail: 18,
  generating_seo: 19,
  completed: 20,
  failed: -1,
};

function isReady(currentStatus: ProjectStatus, requiredStatus: ProjectStatus | null): boolean {
  if (requiredStatus === null) return true;
  if (currentStatus === "failed") return true; // allow retry/resume after a failure
  return STATUS_RANK[currentStatus] >= STATUS_RANK[requiredStatus];
}

export function StageActions({ projectId, status }: { projectId: string; status: ProjectStatus }) {
  const triggerStage = useTriggerStage(projectId);
  const triggerFullPipeline = useTriggerFullPipeline(projectId);
  const isBusy = status !== "draft" && status !== "failed" && !status.endsWith("_ready") && status !== "completed";

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Button
          onClick={() => triggerFullPipeline.mutate()}
          disabled={triggerFullPipeline.isPending || isBusy}
        >
          {triggerFullPipeline.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          Run full pipeline
        </Button>
        <span className="text-xs text-[var(--color-text-muted)]">
          or run stages individually to review each step first
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {STAGE_SEQUENCE.map(({ stage, label, readyAfter }) => (
          <Button
            key={stage}
            variant="secondary"
            size="sm"
            disabled={!isReady(status, readyAfter) || isBusy || triggerStage.isPending}
            onClick={() => triggerStage.mutate(stage)}
          >
            {label}
          </Button>
        ))}
      </div>
    </div>
  );
}
