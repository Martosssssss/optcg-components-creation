import type { RefObject } from "react";
import { ImageUp, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";

export function ImageControls({
  uploaded,
  fileRef,
  onFile,
  onReset,
}: {
  uploaded: string | null;
  fileRef: RefObject<HTMLInputElement>;
  onFile: (file?: File | null) => void;
  onReset: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button type="button" variant="outline" size="sm" onClick={() => fileRef.current?.click()}>
        <ImageUp className="h-4 w-4" />
        Subir imagen
      </Button>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={onReset}
        disabled={!uploaded}
      >
        <RotateCcw className="h-4 w-4" />
        Restablecer
      </Button>
      <input
        ref={fileRef}
        type="file"
        accept="image/png,image/jpeg"
        className="hidden"
        onChange={(e) => onFile(e.target.files?.[0])}
      />
      {uploaded && (
        <span className="text-xs text-muted-foreground">Imagen nueva subida</span>
      )}
    </div>
  );
}