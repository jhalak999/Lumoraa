import { Link } from "react-router-dom";
import { FolderKanban, CheckCircle2, Loader2, XCircle, Film, Clock, ArrowRight } from "lucide-react";
import { useDashboardStats } from "@/features/dashboard/api/dashboard-api";
import { StatCard } from "@/features/dashboard/components/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getStatusBadgeVariant, getStatusLabel } from "@/lib/project-status";
import type { ProjectStatus } from "@/types/api";

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remaining = Math.round(seconds % 60);
  if (minutes === 0) return `${remaining}s`;
  return `${minutes}m ${remaining}s`;
}

export function DashboardPage() {
  const { data, isLoading, isError, refetch } = useDashboardStats();

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-[var(--color-amber)]" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <Card className="p-8 text-center">
        <p className="text-[var(--color-text-secondary)]">Couldn't load your dashboard.</p>
        <button onClick={() => refetch()} className="mt-3 text-sm font-medium text-[var(--color-amber)] hover:underline">
          Try again
        </button>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="font-display text-2xl font-medium tracking-tight">Studio overview</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">Everything moving through your pipeline right now.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total projects" value={data.total_projects} icon={FolderKanban} />
        <StatCard label="In progress" value={data.in_progress_projects} icon={Loader2} accent="cyan" />
        <StatCard label="Completed" value={data.completed_projects} icon={CheckCircle2} accent="amber" />
        <StatCard label="Failed" value={data.failed_projects} icon={XCircle} accent="danger" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent projects</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-1">
            {data.recent_projects.length === 0 ? (
              <p className="py-6 text-center text-sm text-[var(--color-text-muted)]">
                No projects yet — start your first one from the sidebar.
              </p>
            ) : (
              data.recent_projects.map((project) => (
                <Link
                  key={project.id}
                  to={`/projects/${project.id}`}
                  className="group flex items-center justify-between rounded-md px-3 py-3 transition-colors hover:bg-[var(--color-surface-raised)]"
                >
                  <div className="flex items-center gap-3">
                    <Film className="h-4 w-4 text-[var(--color-text-muted)]" />
                    <span className="text-sm font-medium">{project.title}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={getStatusBadgeVariant(project.status as ProjectStatus)}>
                      {getStatusLabel(project.status as ProjectStatus)}
                    </Badge>
                    <ArrowRight className="h-4 w-4 text-[var(--color-text-muted)] opacity-0 transition-opacity group-hover:opacity-100" />
                  </div>
                </Link>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-[var(--color-amber)]" />
              This month
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-mono text-2xl font-medium">{formatDuration(data.total_render_seconds_this_month)}</p>
            <p className="mt-1 text-sm text-[var(--color-text-muted)]">of finished runtime rendered</p>
            <div className="mt-5 border-t border-[var(--color-border)] pt-4">
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
                Videos generated
              </p>
              <p className="font-mono text-xl font-medium">{data.total_videos_generated}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
