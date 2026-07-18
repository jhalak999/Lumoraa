import type { ProjectStatus } from "@/types/api";

/** Ordered pipeline stages — this order is literal, real sequence information,
 * which is why the Pipeline Rail is allowed to use numbered/ordered markers. */
export const PIPELINE_STAGES: { status: ProjectStatus; label: string }[] = [
  { status: "research_ready", label: "Research" },
  { status: "script_ready", label: "Script" },
  { status: "scenes_ready", label: "Scenes" },
  { status: "image_prompts_ready", label: "Image prompts" },
  { status: "images_ready", label: "Images" },
  { status: "voice_ready", label: "Voice" },
  { status: "subtitles_ready", label: "Subtitles" },
  { status: "video_ready", label: "Video" },
  { status: "completed", label: "Thumbnail + SEO" },
];

const STATUS_LABELS: Record<ProjectStatus, string> = {
  draft: "Draft",
  researching: "Researching…",
  research_ready: "Research ready",
  scripting: "Writing script…",
  script_ready: "Script ready",
  planning_scenes: "Planning scenes…",
  scenes_ready: "Scenes ready",
  generating_image_prompts: "Generating image prompts…",
  image_prompts_ready: "Image prompts ready",
  generating_images: "Generating images…",
  images_ready: "Images ready",
  generating_voice: "Generating voice…",
  voice_ready: "Voice ready",
  generating_subtitles: "Generating subtitles…",
  subtitles_ready: "Subtitles ready",
  rendering_video: "Rendering video…",
  video_ready: "Video ready",
  generating_thumbnail: "Generating thumbnail…",
  generating_seo: "Generating SEO metadata…",
  seo_ready: "SEO ready",
  completed: "Completed",
  failed: "Failed",
};

export function getStatusLabel(status: ProjectStatus): string {
  return STATUS_LABELS[status];
}

export function isStatusInProgress(status: ProjectStatus): boolean {
  return status.startsWith("generating_") || status.startsWith("planning_") || status === "researching" || status === "scripting" || status === "rendering_video";
}

export function getStatusBadgeVariant(status: ProjectStatus): "amber" | "cyan" | "danger" | "default" {
  if (status === "failed") return "danger";
  if (status === "completed") return "amber";
  if (isStatusInProgress(status)) return "cyan";
  return "default";
}

/** How many of the 9 pipeline stages are complete, for progress displays. */
export function getPipelineProgress(status: ProjectStatus): { completedStages: number; totalStages: number } {
  const totalStages = PIPELINE_STAGES.length;
  if (status === "failed" || status === "draft") return { completedStages: 0, totalStages };
  const index = PIPELINE_STAGES.findIndex((s) => s.status === status);
  if (index >= 0) return { completedStages: index + 1, totalStages };

  // Status is an intermediate "in progress" state (e.g. "generating_images")
  // that sits between two ready-states — count the last fully-reached stage.
  const order: ProjectStatus[] = [
    "draft",
    "researching",
    "research_ready",
    "scripting",
    "script_ready",
    "planning_scenes",
    "scenes_ready",
    "generating_image_prompts",
    "image_prompts_ready",
    "seo_ready",
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
    "completed",
  ];  const currentIndex = order.indexOf(status);
  const completedStages = PIPELINE_STAGES.reduce(
    (acc, stage, i) => (order.indexOf(stage.status) <= currentIndex ? i : acc),
    0
  );
  return { completedStages, totalStages };
}
