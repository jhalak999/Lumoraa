import { PIPELINE_STAGES, isStatusInProgress } from "@/lib/project-status";
import { cn } from "@/lib/utils";
import type { ProjectStatus } from "@/types/api";
import { Check, Loader2 } from "lucide-react";

const STAGE_ORDER: ProjectStatus[] = [
  "draft",
  "researching",
  "research_ready",
  "scripting",
  "script_ready",
  "planning_scenes",
  "scenes_ready",
  "generating_image_prompts",
  "image_prompts_ready",
  "generating_images",
  "images_ready",
  "generating_voice",
  "voice_ready",
  "generating_subtitles",
  "subtitles_ready",
  "rendering_video",
  "video_ready",
  "generating_thumbnail",
  "generating_seo",
  "seo_ready",
  "completed",
];

/** This is the studio's signature element: a literal production timeline for
 * an actually-ordered process, not a decorative numbered list. */
export function PipelineRail({ status }: { status: ProjectStatus }) {
  const currentIndex = status === "failed" ? -1 : STAGE_ORDER.indexOf(status);

  return (
    <div className="w-full overflow-x-auto pb-2">
      <ol className="flex min-w-max items-center">
        {PIPELINE_STAGES.map((stage, i) => {
          const stageIndex = STAGE_ORDER.indexOf(stage.status);
          const isComplete = currentIndex >= stageIndex;
          const isCurrent =
            currentIndex >= 0 &&
            currentIndex < stageIndex &&
            (i === 0 || STAGE_ORDER.indexOf(PIPELINE_STAGES[i - 1].status) <= currentIndex);
          const isActive = status === stage.status || isCurrent;

          return (
            <li key={stage.status} className="flex items-center">
              <div className="flex flex-col items-center gap-2">
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-mono font-medium transition-colors",
                    isComplete
                      ? "border-[var(--color-amber)] bg-[var(--color-amber)] text-[#171208]"
                      : isActive && isStatusInProgress(status)
                        ? "border-[var(--color-cyan)] text-[var(--color-cyan)]"
                        : "border-[var(--color-border-strong)] text-[var(--color-text-muted)]"
                  )}
                >
                  {isComplete ? (
                    <Check className="h-4 w-4" />
                  ) : isActive && isStatusInProgress(status) ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    i + 1
                  )}
                </div>
                <span
                  className={cn(
                    "whitespace-nowrap text-xs font-medium",
                    isComplete ? "text-[var(--color-text-primary)]" : "text-[var(--color-text-muted)]"
                  )}
                >
                  {stage.label}
                </span>
              </div>
              {i < PIPELINE_STAGES.length - 1 && (
                <div
                  className={cn(
                    "mx-2 h-0.5 w-10 transition-colors",
                    currentIndex >= STAGE_ORDER.indexOf(PIPELINE_STAGES[i + 1].status)
                      ? "bg-[var(--color-amber)]"
                      : "bg-[var(--color-border-strong)]"
                  )}
                />
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
