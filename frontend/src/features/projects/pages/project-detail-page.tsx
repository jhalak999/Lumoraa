import { useParams } from "react-router-dom";
import { Loader2, AlertTriangle } from "lucide-react";
import { useProjectDetail } from "@/features/projects/hooks/use-projects";
import { PipelineRail } from "@/features/generation/components/pipeline-rail";
import { StageActions } from "@/features/generation/components/stage-actions";
import { JobProgressList } from "@/features/generation/components/job-progress-list";
import { ResearchPanel, ScriptPanel, ScenesPanel, SeoPanel } from "@/features/generation/components/output-panels";
import { ImagesGalleryPanel, VoiceAndSubtitlesPanel, FinalVideoPanel } from "@/features/generation/components/media-panels";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getStatusBadgeVariant, getStatusLabel } from "@/lib/project-status";

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: project, isLoading, isError, refetch } = useProjectDetail(projectId);

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--color-amber)]" />
      </div>
    );
  }

  if (isError || !project) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center">
        <p className="text-[var(--color-text-secondary)]">Couldn't load this project.</p>
        <button onClick={() => refetch()} className="text-sm font-medium text-[var(--color-amber)] hover:underline">
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-display text-2xl font-medium tracking-tight">{project.title}</h1>
          <Badge variant={getStatusBadgeVariant(project.status)}>{getStatusLabel(project.status)}</Badge>
        </div>
        <p className="mt-1 max-w-2xl text-sm text-[var(--color-text-muted)]">{project.topic}</p>
      </div>

      {project.status === "failed" && project.error_message && (
        <div className="flex items-start gap-3 rounded-lg border border-[var(--color-danger)]/30 bg-[var(--color-danger-dim)] p-4">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--color-danger)]" />
          <div>
            <p className="text-sm font-medium text-[var(--color-danger)]">This project's last step failed</p>
            <p className="mt-0.5 text-sm text-[var(--color-text-secondary)]">{project.error_message}</p>
          </div>
        </div>
      )}

      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
        <PipelineRail status={project.status} />
      </div>

      <StageActions projectId={project.id} status={project.status} />

      <JobProgressList projectId={project.id} />

      <Tabs defaultValue="script">
        <TabsList>
          <TabsTrigger value="research">Research</TabsTrigger>
          <TabsTrigger value="script">Script</TabsTrigger>
          <TabsTrigger value="scenes">Scenes</TabsTrigger>
          <TabsTrigger value="visuals">Visuals</TabsTrigger>
          <TabsTrigger value="audio">Audio &amp; subtitles</TabsTrigger>
          <TabsTrigger value="final">Final</TabsTrigger>
          <TabsTrigger value="seo">SEO</TabsTrigger>
        </TabsList>

        <TabsContent value="research">
          <ResearchPanel research={project.research_data} />
        </TabsContent>
        <TabsContent value="script">
          <ScriptPanel script={project.script_data} />
        </TabsContent>
        <TabsContent value="scenes">
          <ScenesPanel scenePlan={project.scene_plan} />
        </TabsContent>
        <TabsContent value="visuals">
          <ImagesGalleryPanel assets={project.assets} />
        </TabsContent>
        <TabsContent value="audio">
          <VoiceAndSubtitlesPanel assets={project.assets} />
        </TabsContent>
        <TabsContent value="final">
          <FinalVideoPanel assets={project.assets} />
        </TabsContent>
        <TabsContent value="seo">
          <SeoPanel seo={project.seo_metadata} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
