import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";

export function SliderControls({
  zoom,
  posX,
  posY,
  onZoom,
  onPosX,
  onPosY,
}: {
  zoom: number;
  posX: number;
  posY: number;
  onZoom: (v: number) => void;
  onPosX: (v: number) => void;
  onPosY: (v: number) => void;
}) {
  const rows = [
    { id: "zoom", label: `Zoom de la imagen (${zoom}%)`, value: zoom, min: 100, max: 220, set: onZoom },
    { id: "posX", label: `Posición horizontal (${posX}%)`, value: posX, min: 0, max: 100, set: onPosX },
    { id: "posY", label: `Posición vertical (${posY}%)`, value: posY, min: 0, max: 100, set: onPosY },
  ];

  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <div key={row.id}>
          <Label className="text-xs font-medium text-foreground">{row.label}</Label>
          <Slider
            value={[row.value]}
            min={row.min}
            max={row.max}
            step={1}
            onValueChange={(v) => row.set(v[0])}
          />
        </div>
      ))}
    </div>
  );
}