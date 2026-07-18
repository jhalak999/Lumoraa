import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { AssetDownloadButton } from "@/features/generation/components/asset-download-button";
import { EmptyPanel } from "@/features/generation/components/output-panels";
import type { Asset } from "@/types/api";

function assetsOfType(assets: Asset[], type: Asset["asset_type"]) {
  return assets.filter((a) => a.asset_type === type).sort((a, b) => (a.sequence_index ?? 0) - (b.sequence_index ?? 0));
}

export function ImagesGalleryPanel({ assets }: { assets: Asset[] }) {
  const images = assetsOfType(assets, "scene_image");
  if (images.length === 0) return <EmptyPanel message="Generate images to see scene visuals here." />;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scene images</CardTitle>
        <CardDescription>{images.length} scenes rendered</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {images.map((image) => (
            <div key={image.id} className="group relative overflow-hidden rounded-md border border-[var(--color-border)]">
              <img src={image.public_url} alt={`Scene ${image.sequence_index}`} className="aspect-[9/16] w-full object-cover" />
              <div className="absolute inset-x-0 bottom-0 flex items-center justify-between bg-black/60 px-2 py-1 text-xs opacity-0 backdrop-blur-sm transition-opacity group-hover:opacity-100">
                <span className="font-mono">#{image.sequence_index}</span>
                <span className="text-[var(--color-text-muted)]">{image.provider_used}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function VoiceAndSubtitlesPanel({ assets }: { assets: Asset[] }) {
  const [voice] = assetsOfType(assets, "voice_audio");
  const [subtitles] = assetsOfType(assets, "subtitle_file");

  if (!voice && !subtitles) return <EmptyPanel message="Generate voice and subtitles to review them here." />;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Voice &amp; subtitles</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {voice && (
          <div className="flex flex-col gap-2">
            <audio controls src={voice.public_url} className="w-full" />
            <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)]">
              <span>Synthesized via {voice.provider_used}</span>
              <AssetDownloadButton asset={voice} label="Download audio" />
            </div>
          </div>
        )}
        {subtitles && (
          <div className="flex items-center justify-between border-t border-[var(--color-border)] pt-4 text-sm">
            <span className="text-[var(--color-text-secondary)]">Captions (.srt)</span>
            <AssetDownloadButton asset={subtitles} label="Download subtitles" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function FinalVideoPanel({ assets }: { assets: Asset[] }) {
  const [video] = assetsOfType(assets, "final_video");
  const [thumbnail] = assetsOfType(assets, "thumbnail");

  if (!video && !thumbnail) return <EmptyPanel message="Render the video to watch and download the final cut here." />;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      {video && (
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Final video</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <video controls src={video.public_url} className="mx-auto aspect-[9/16] max-h-[520px] rounded-md bg-black" />
            <div className="flex justify-end">
              <AssetDownloadButton asset={video} label="Download video" />
            </div>
          </CardContent>
        </Card>
      )}
      {thumbnail && (
        <Card>
          <CardHeader>
            <CardTitle>Thumbnail</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <img src={thumbnail.public_url} alt="Thumbnail" className="aspect-[9/16] w-full rounded-md object-cover" />
            <AssetDownloadButton asset={thumbnail} label="Download thumbnail" />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
