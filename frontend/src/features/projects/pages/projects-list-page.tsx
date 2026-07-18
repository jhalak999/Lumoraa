import * as React from "react";
import { Loader2, FolderKanban } from "lucide-react";
import { Link } from "react-router-dom";
import { useProjectsList, useDeleteProject } from "@/features/projects/hooks/use-projects";
import { ProjectCard } from "@/features/projects/components/project-card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

export function ProjectsListPage() {
  const { data, isLoading, isError, refetch } = useProjectsList();
  const deleteProject = useDeleteProject();
  const [pendingDeleteId, setPendingDeleteId] = React.useState<string | null>(null);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-medium tracking-tight">Projects</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">Every video moving through the studio.</p>
        </div>
        <Button asChild>
          <Link to="/projects/new">New project</Link>
        </Button>
      </div>

      {isLoading && (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-[var(--color-amber)]" />
        </div>
      )}

      {isError && (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <p className="text-[var(--color-text-secondary)]">Couldn't load your projects.</p>
          <button onClick={() => refetch()} className="text-sm font-medium text-[var(--color-amber)] hover:underline">
            Try again
          </button>
        </div>
      )}

      {data && data.items.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-[var(--color-border-strong)] py-20 text-center">
          <FolderKanban className="h-8 w-8 text-[var(--color-text-muted)]" />
          <p className="font-display text-lg">No projects yet</p>
          <p className="max-w-sm text-sm text-[var(--color-text-muted)]">
            Give Lumora a topic and it'll research it, write the script, plan scenes, and render a finished video.
          </p>
          <Button asChild className="mt-2">
            <Link to="/projects/new">Start your first project</Link>
          </Button>
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((project) => (
            <ProjectCard key={project.id} project={project} onDelete={setPendingDeleteId} />
          ))}
        </div>
      )}

      <Dialog open={Boolean(pendingDeleteId)} onOpenChange={(open) => !open && setPendingDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete this project?</DialogTitle>
            <DialogDescription>
              This permanently removes the project and every generated asset — research, script, images, voice, and video.
              This can't be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setPendingDeleteId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (pendingDeleteId) deleteProject.mutate(pendingDeleteId);
                setPendingDeleteId(null);
              }}
            >
              Delete project
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
