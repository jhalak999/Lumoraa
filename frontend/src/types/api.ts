export type ContentTone =
  | "educational"
  | "entertaining"
  | "dramatic"
  | "professional"
  | "casual"
  | "inspirational";

export type ProjectStatus =
  | "draft"
  | "researching"
  | "research_ready"
  | "scripting"
  | "script_ready"
  | "planning_scenes"
  | "scenes_ready"
  | "generating_image_prompts"
  | "image_prompts_ready"
  | "generating_images"
  | "images_ready"
  | "generating_voice"
  | "voice_ready"
  | "generating_subtitles"
  | "subtitles_ready"
  | "rendering_video"
  | "video_ready"
  | "generating_thumbnail"
  | "generating_seo"
  | "seo_ready"
  | "completed"
  | "failed";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Project {
  id: string;
  title: string;
  topic: string;
  tone: ContentTone;
  target_duration_seconds: number;
  status: ProjectStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchFact {
  claim: string;
  supporting_detail: string;
  relevance_score: number;
}

export interface ResearchOutput {
  topic_summary: string;
  key_facts: ResearchFact[];
  suggested_angle: string;
  target_audience: string;
}

export interface ScriptLine {
  order: number;
  speaker_note: string;
  text: string;
}

export interface ScriptOutput {
  hook: string;
  lines: ScriptLine[];
  call_to_action: string;
  estimated_duration_seconds: number;
  word_count: number;
}

export interface Scene {
  order: number;
  script_line_orders: number[];
  visual_description: string;
  duration_seconds: number;
  camera_motion: string;
}

export interface ScenePlanOutput {
  scenes: Scene[];
  total_duration_seconds: number;
  visual_style: string;
}

export interface ImagePrompt {
  scene_order: number;
  prompt: string;
  negative_prompt: string;
  aspect_ratio: string;
}

export interface ImagePromptOutput {
  prompts: ImagePrompt[];
  style_reference: string;
}

export interface SeoOutput {
  titles: string[];
  description: string;
  hashtags: string[];
  keywords: string[];
}

export interface Asset {
  id: string;
  asset_type: "scene_image" | "voice_audio" | "subtitle_file" | "final_video" | "thumbnail";
  public_url: string;
  sequence_index: number | null;
  provider_used: string | null;
  created_at: string;
}

export interface ProjectDetail extends Project {
  research_data: ResearchOutput | null;
  script_data: ScriptOutput | null;
  scene_plan: ScenePlanOutput | null;
  image_prompts: ImagePromptOutput | null;
  seo_metadata: SeoOutput | null;
  assets: Asset[];
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
}

export type JobStage =
  | "research"
  | "script"
  | "scene_plan"
  | "image_prompts"
  | "images"
  | "voice"
  | "subtitles"
  | "video"
  | "thumbnail"
  | "seo"
  | "full_pipeline";

export type JobStatus = "pending" | "running" | "succeeded" | "failed";

export interface Job {
  id: string;
  project_id: string;
  stage: JobStage;
  status: JobStatus;
  progress_percent: number;
  progress_message: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  total_projects: number;
  completed_projects: number;
  in_progress_projects: number;
  failed_projects: number;
  total_videos_generated: number;
  total_render_seconds_this_month: number;
  projects_by_status: Record<string, number>;
  recent_projects: Array<{ id: string; title: string; status: string; created_at: string }>;
}

export interface ApiErrorBody {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}
