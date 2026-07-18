import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { useCreateProject } from "@/features/projects/hooks/use-projects";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { ContentTone } from "@/types/api";

const TONE_OPTIONS: { value: ContentTone; label: string }[] = [
  { value: "educational", label: "Educational" },
  { value: "entertaining", label: "Entertaining" },
  { value: "dramatic", label: "Dramatic" },
  { value: "professional", label: "Professional" },
  { value: "casual", label: "Casual" },
  { value: "inspirational", label: "Inspirational" },
];

const schema = z.object({
  title: z.string().min(1, "Give the project a name.").max(255),
  topic: z.string().min(1, "Describe what the video is about.").max(5000),
  tone: z.custom<ContentTone>(),
  target_duration_seconds: z.number().min(15).max(600),
});
type FormValues = z.infer<typeof schema>;

export function NewProjectPage() {
  const createProject = useCreateProject();
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { tone: "educational", target_duration_seconds: 60 },
  });

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6">
        <h1 className="font-display text-2xl font-medium tracking-tight">New project</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Give Lumora a topic — it handles research, script, scenes, voice, subtitles, and the final render.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Project brief</CardTitle>
          <CardDescription>The more specific the topic, the sharper the research angle.</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit((values) => createProject.mutate(values))}
            className="flex flex-col gap-5"
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="title">Title</Label>
              <Input id="title" placeholder="Why octopuses have three hearts" {...register("title")} />
              {errors.title && <p className="text-xs text-[var(--color-danger)]">{errors.title.message}</p>}
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="topic">Topic</Label>
              <Textarea
                id="topic"
                rows={4}
                placeholder="The biology and evolutionary reason octopuses evolved three hearts, and what happens to their circulation when they swim."
                {...register("topic")}
              />
              {errors.topic && <p className="text-xs text-[var(--color-danger)]">{errors.topic.message}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <Label>Tone</Label>
                <Controller
                  control={control}
                  name="tone"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {TONE_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label htmlFor="duration">Target duration (seconds)</Label>
                <Input
                  id="duration"
                  type="number"
                  min={15}
                  max={600}
                  {...register("target_duration_seconds", { valueAsNumber: true })}
                />
              </div>
            </div>

            <Button type="submit" disabled={createProject.isPending} className="mt-2">
              {createProject.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Create project
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
