import { Link } from "react-router-dom";
import { Film, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { getPipelineProgress, getStatusBadgeVariant, getStatusLabel, isStatusInProgress } from "@/lib/project-status";
import type { Project } from "@/types/api";

export function ProjectCard({ project, onDelete }: { project: Project; onDelete: (id: string) => void }) {
  const { completedStages, totalStages } = getPipelineProgress(project.status);
  const progressPercent = Math.round((completedStages / totalStages) * 100);

  return (
    <Card className="group relative flex flex-col overflow-hidden">
      <Link to={`/projects/${project.id}`} className="flex flex-1 flex-col p-5">
        <div className="mb-3 flex items-start justify-between gap-2">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-[var(--color-surface-raised)] text-[var(--color-amber)]">
            <Film className="h-4 w-4" />
          </div>
          <Badge variant={getStatusBadgeVariant(project.status)}>{getStatusLabel(project.status)}</Badge>
        </div>
        <h3 className="font-display text-base font-medium leading-snug">{project.title}</h3>
        <p className="mt-1 line-clamp-2 text-sm text-[var(--color-text-muted)]">{project.topic}</p>

        <div className="mt-4">
          <div className="mb-1.5 flex items-center justify-between text-xs text-[var(--color-text-muted)]">
            <span>Pipeline progress</span>
            <span className="font-mono">{completedStages}/{totalStages}</span>
          </div>
          <Progress value={progressPercent} isLive={isStatusInProgress(project.status)} />
        </div>
      </Link>

      <button
        onClick={(e) => {
          e.preventDefault();
          onDelete(project.id);
        }}
        aria-label={`Delete ${project.title}`}
        className="absolute right-3 top-3 rounded-md p-1.5 text-[var(--color-text-muted)] opacity-0 transition-opacity hover:bg-[var(--color-danger-dim)] hover:text-[var(--color-danger)] group-hover:opacity-100"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </Card>
  );
}
