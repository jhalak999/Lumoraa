import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Asset } from "@/types/api";

export function AssetDownloadButton({ asset, label }: { asset: Asset; label: string }) {
  const downloadUrl = `/api/v1/assets/${asset.id}/download`;

  return (
    <Button asChild variant="secondary" size="sm">
      <a href={downloadUrl} download>
        <Download className="h-3.5 w-3.5" />
        {label}
      </a>
    </Button>
  );
}
