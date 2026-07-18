import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ResearchOutput, ScriptOutput, ScenePlanOutput, SeoOutput } from "@/types/api";

export function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-[var(--color-border-strong)] text-sm text-[var(--color-text-muted)]">
      {message}
    </div>
  );
}

export function ResearchPanel({ research }: { research: ResearchOutput | null }) {
  if (!research) return <EmptyPanel message="Run research to see key facts and the narrative angle here." />;
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Angle</CardTitle>
          <CardDescription>{research.target_audience}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-[var(--color-text-secondary)]">{research.topic_summary}</p>
          <p className="mt-3 rounded-md bg-[var(--color-surface-raised)] p-3 text-sm font-medium text-[var(--color-amber)]">
            {research.suggested_angle}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Key facts</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {research.key_facts.map((fact, i) => (
            <div key={i} className="border-b border-[var(--color-border)] pb-3 last:border-0 last:pb-0">
              <p className="text-sm font-medium">{fact.claim}</p>
              <p className="mt-1 text-sm text-[var(--color-text-muted)]">{fact.supporting_detail}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export function ScriptPanel({ script }: { script: ScriptOutput | null }) {
  if (!script) return <EmptyPanel message="Write the script to see the narration line-by-line here." />;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Narration</CardTitle>
        <CardDescription>
          {script.word_count} words · ~{script.estimated_duration_seconds}s
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="rounded-md bg-[var(--color-surface-raised)] p-3 text-sm font-medium text-[var(--color-amber)]">
          {script.hook}
        </p>
        {script.lines.map((line) => (
          <div key={line.order} className="flex gap-3 text-sm">
            <span className="w-6 shrink-0 font-mono text-[var(--color-text-muted)]">{line.order}</span>
            <div>
              <p>{line.text}</p>
              <p className="mt-0.5 text-xs italic text-[var(--color-text-muted)]">{line.speaker_note}</p>
            </div>
          </div>
        ))}
        <p className="mt-2 border-t border-[var(--color-border)] pt-3 text-sm font-medium text-[var(--color-cyan)]">
          {script.call_to_action}
        </p>
      </CardContent>
    </Card>
  );
}

export function ScenesPanel({ scenePlan }: { scenePlan: ScenePlanOutput | null }) {
  if (!scenePlan) return <EmptyPanel message="Plan scenes to see the shot-by-shot breakdown here." />;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Scene plan</CardTitle>
        <CardDescription>{scenePlan.visual_style}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {scenePlan.scenes.map((scene) => (
          <div key={scene.order} className="flex gap-3 rounded-md bg-[var(--color-surface-raised)] p-3 text-sm">
            <span className="w-6 shrink-0 font-mono text-[var(--color-text-muted)]">{scene.order}</span>
            <div className="flex-1">
              <p>{scene.visual_description}</p>
              <div className="mt-1.5 flex gap-2 text-xs text-[var(--color-text-muted)]">
                <span>{scene.camera_motion}</span>
                <span>·</span>
                <span className="font-mono">{scene.duration_seconds.toFixed(1)}s</span>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function SeoPanel({ seo }: { seo: SeoOutput | null }) {
  if (!seo) return <EmptyPanel message="Generate SEO metadata to see title and description options here." />;
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Title options</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {seo.titles.map((title, i) => (
            <div key={i} className="flex items-center gap-2 rounded-md bg-[var(--color-surface-raised)] p-3 text-sm">
              {i === 0 && <Badge variant="amber">Best</Badge>}
              <span>{title}</span>
            </div>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Description</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-[var(--color-text-secondary)]">{seo.description}</p>
          <div className="flex flex-wrap gap-1.5">
            {seo.hashtags.map((tag) => (
              <Badge key={tag} variant="cyan">
                #{tag.replace(/^#/, "")}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
