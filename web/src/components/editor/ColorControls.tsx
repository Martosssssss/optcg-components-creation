import { Label } from "@/components/ui/label";

export function ColorControls({
  isCard,
  useColors,
  twoColors,
  color1,
  color2,
  onToggle,
  onTwoColors,
  onColor1,
  onColor2,
}: {
  isCard: boolean;
  useColors: boolean;
  twoColors: boolean;
  color1: string;
  color2: string;
  onToggle: (v: boolean) => void;
  onTwoColors: (v: boolean) => void;
  onColor1: (v: string) => void;
  onColor2: (v: string) => void;
}) {
  return (
    <div className="rounded-lg border border-border bg-muted p-3">
      <div className="flex items-center justify-between">
        <Label htmlFor="editor-colors" className="text-xs font-medium">
          {isCard ? "Color de la carta" : "Colores del degradado"}
        </Label>
        <input
          id="editor-colors"
          type="checkbox"
          checked={useColors}
          onChange={(e) => onToggle(e.target.checked)}
        />
      </div>
      {useColors && (
        <div className="mt-2 space-y-2">
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={color1}
              onChange={(e) => onColor1(e.target.value)}
              className="h-8 w-12 cursor-pointer rounded border border-border bg-card"
              aria-label="Color 1"
            />
            {!isCard && (
              <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <input
                  type="checkbox"
                  checked={twoColors}
                  onChange={(e) => onTwoColors(e.target.checked)}
                />
                2 colores
              </label>
            )}
          </div>
          {!isCard && twoColors && (
            <input
              type="color"
              value={color2}
              onChange={(e) => onColor2(e.target.value)}
              className="h-8 w-12 cursor-pointer rounded border border-border bg-card"
              aria-label="Color 2"
            />
          )}
        </div>
      )}
    </div>
  );
}