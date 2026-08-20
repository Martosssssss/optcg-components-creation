import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCardEditor } from "@/hooks/useCardEditor";
import type { DeckEntry } from "@/types";
import type { DeckPatch } from "@/hooks/useDeck";
import { ColorControls } from "./ColorControls";
import { ImageControls } from "./ImageControls";
import { PreviewPane } from "./PreviewPane";
import { SliderControls } from "./SliderControls";

export function CardEditorDialog({
  entry,
  index,
  onOpenChange,
  onApply,
}: {
  entry: DeckEntry | null;
  index: number;
  onOpenChange: (open: boolean) => void;
  onApply: (index: number, patch: DeckPatch) => void;
}) {
  const editor = useCardEditor(entry, index, onApply, onOpenChange);
  const {
    open,
    isCard,
    name,
    code,
    qty,
    useColors,
    twoColors,
    color1,
    color2,
    zoom,
    posX,
    posY,
    uploaded,
    previewPng,
    busy,
    status,
    fileRef,
    cardData,
    setName,
    setCode,
    setQty,
    setUseColors,
    setTwoColors,
    setColor1,
    setColor2,
    setZoom,
    setPosX,
    setPosY,
    handleFile,
    handleResetImage,
    handlePreview,
    handleApply,
    edit,
  } = editor;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle>Editar carta</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.2fr_1fr]">
          <PreviewPane entry={entry} cardData={cardData} previewPng={previewPng} />

          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <Label htmlFor="editor-name">Nombre</Label>
                <Input
                  id="editor-name"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    edit();
                  }}
                  maxLength={80}
                  spellCheck={false}
                />
              </div>
              <div>
                <Label htmlFor="editor-code">Código</Label>
                <Input
                  id="editor-code"
                  value={code}
                  onChange={(e) => {
                    setCode(e.target.value);
                    edit();
                  }}
                  maxLength={16}
                  spellCheck={false}
                />
              </div>
              <div>
                <Label htmlFor="editor-qty">Cantidad</Label>
                <Input
                  id="editor-qty"
                  value={qty}
                  onChange={(e) => {
                    setQty(e.target.value);
                    edit();
                  }}
                  maxLength={8}
                  placeholder="x4"
                  spellCheck={false}
                />
              </div>
            </div>

            <ColorControls
              isCard={isCard}
              useColors={useColors}
              twoColors={twoColors}
              color1={color1}
              color2={color2}
              onToggle={(v) => {
                setUseColors(v);
                edit();
              }}
              onTwoColors={(v) => {
                setTwoColors(v);
                edit();
              }}
              onColor1={(v) => {
                setColor1(v);
                edit();
              }}
              onColor2={(v) => {
                setColor2(v);
                edit();
              }}
            />

            <SliderControls
              zoom={zoom}
              posX={posX}
              posY={posY}
              onZoom={(v) => {
                setZoom(v);
                edit();
              }}
              onPosX={(v) => {
                setPosX(v);
                edit();
              }}
              onPosY={(v) => {
                setPosY(v);
                edit();
              }}
            />

            <ImageControls
              uploaded={uploaded}
              fileRef={fileRef}
              onFile={handleFile}
              onReset={handleResetImage}
            />

            <div className="flex flex-wrap items-center gap-2">
              <Button type="button" variant="secondary" size="sm" onClick={handlePreview} disabled={busy}>
                <Sparkles className="h-4 w-4" />
                Previsualizar
              </Button>
              <Button type="button" onClick={handleApply} disabled={busy}>
                {busy ? "Renderizando…" : "Aplicar"}
              </Button>
            </div>

            {status && <p className="text-xs text-muted-foreground">{status}</p>}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}