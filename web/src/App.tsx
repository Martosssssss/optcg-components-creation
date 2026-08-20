import { useCallback, useEffect, useState } from "react";

import * as api from "@/api";
import { CardEditorDialog } from "@/components/editor/CardEditorDialog";
import { ResultsGrid } from "@/components/ResultsGrid";
import { StepInput } from "@/components/StepInput";
import { StepPicker } from "@/components/StepPicker";
import { useDeck } from "@/hooks/useDeck";
import { downloadBlob } from "@/lib/helpers";
import type { GenerateError } from "@/types";

type BusyAction = "generate" | "zip" | null;

export default function App() {
  const [components, setComponents] = useState<string[]>([]);
  const [component, setComponent] = useState<string | null>(null);
  const [errors, setErrors] = useState<GenerateError[]>([]);
  const [busy, setBusy] = useState<BusyAction>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const { deck, replaceAll, applyEdit, clear } = useDeck();

  useEffect(() => {
    api
      .getComponents()
      .then((list) => {
        if (list.length) setComponents(list);
      })
      .catch(() => {
        setComponents(["card", "leader"]);
      });
  }, []);

  const handleGenerate = useCallback(
    async (text: string) => {
      if (!component) return;
      setBusy("generate");
      setErrors([]);
      try {
        const res = await api.generate(text, component);
        replaceAll(res.cards, component);
        setErrors(res.errors);
      } catch (err) {
        setErrors([
          { code: "error", reason: err instanceof Error ? err.message : String(err) },
        ]);
        clear();
      } finally {
        setBusy(null);
      }
    },
    [component, replaceAll, clear]
  );

  const handleDownloadAll = async () => {
    if (!deck.length) return;
    setBusy("zip");
    try {
      const blob = await api.zip(
        deck.map((e) => ({ filename: `${e.code}.png`, png_b64: e.png_b64 }))
      );
      downloadBlob(blob, "cartas.zip");
    } catch (err) {
      alert(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  };

  const handleSelectComponent = (name: string) => {
    setComponent(name);
    setErrors([]);
    clear();
  };

  const editingEntry = editingIndex !== null ? deck[editingIndex] ?? null : null;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/60 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-6 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-foreground font-serif text-lg font-bold text-background">
            OP
          </div>
          <div>
            <h1 className="font-serif text-lg font-semibold tracking-tight text-foreground">
              Cartas One Piece
            </h1>
            <p className="text-xs text-muted-foreground">Generador y editor de cartas</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-10 px-6 py-8">
        {!component ? (
          <StepPicker components={components} onSelect={handleSelectComponent} />
        ) : (
          <>
            <StepInput
              component={component}
              busy={busy === "generate"}
              onGenerate={handleGenerate}
              onBack={() => setComponent(null)}
            />
            <ResultsGrid
              deck={deck}
              errors={errors}
              busyZip={busy === "zip"}
              onEdit={setEditingIndex}
              onDownloadAll={handleDownloadAll}
              onClear={clear}
            />
          </>
        )}
      </main>

      <CardEditorDialog
        entry={editingEntry}
        index={editingIndex ?? 0}
        onOpenChange={(open) => {
          if (!open) setEditingIndex(null);
        }}
        onApply={applyEdit}
      />
    </div>
  );
}