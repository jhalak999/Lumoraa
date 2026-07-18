import { CheckCircle2, XCircle, Loader2, Clock } from "lucide-react";
import { useProjectJobs } from "@/features/generation/hooks/use-generation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const STAGE_LABELS: Record<string, string> = {
  research: "Research",
  script: "Script",
  scene_plan: "Scene plan",
  image_prompts: "Image prompts",
  images: "Images",
  voice: "Voice",
  subtitles: "Subtitles",
  video: "Video render",
  thumbnail: "Thumbnail",
  seo: "SEO metadata",
  full_pipeline: "Full pipeline",
};

export function JobProgressList({ projectId }: { projectId: string }) {
  const { data: jobs } = useProjectJobs(projectId);

  if (!jobs || jobs.length === 0) return null;

  const recentJobs = [...jobs].slice(0, 6);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Activity</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-1">
        {recentJobs.map((job) => (
          <div key={job.id} className="flex items-center justify-between rounded-md px-2 py-2 text-sm">
            <div className="flex items-center gap-2.5">
              {job.status === "succeeded" && <CheckCircle2 className="h-4 w-4 text-[var(--color-amber)]" />}
              {job.status === "failed" && <XCircle className="h-4 w-4 text-[var(--color-danger)]" />}
              {job.status === "running" && <Loader2 className="h-4 w-4 animate-spin text-[var(--color-cyan)]" />}
              {job.status === "pending" && <Clock className="h-4 w-4 text-[var(--color-text-muted)]" />}
              <span className="font-medium">{STAGE_LABELS[job.stage] ?? job.stage}</span>
            </div>
            {job.status === "failed" && job.error_message && (
              <span className="max-w-xs truncate text-xs text-[var(--color-danger)]" title={job.error_message}>
                {job.error_message}
              </span>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
