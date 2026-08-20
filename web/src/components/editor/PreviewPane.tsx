import { Card } from "@/cards/Card";
import { CardPreview } from "@/cards/CardPreview";
import { Leader } from "@/cards/Leader";
import type { CardData } from "@/cards/types";
import type { DeckEntry } from "@/types";

export function PreviewPane({
  entry,
  cardData,
  previewPng,
}: {
  entry: DeckEntry | null;
  cardData: CardData;
  previewPng: string | null;
}) {
  return (
    <div className="checker rounded-lg border border-border p-3">
      {previewPng ? (
        <img
          src={`data:image/png;base64,${previewPng}`}
          alt="Vista previa exportada"
          className="w-full"
        />
      ) : entry?.component === "leader" ? (
        <CardPreview>
          <Leader {...cardData} />
        </CardPreview>
      ) : (
        <CardPreview>
          <Card {...cardData} />
        </CardPreview>
      )}
      <p className="mt-2 text-center text-xs text-muted-foreground">
        {previewPng ? "Vista previa exportada (PNG)" : "Vista previa en tiempo real"}
      </p>
    </div>
  );
}