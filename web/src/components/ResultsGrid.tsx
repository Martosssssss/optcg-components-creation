import { Download, Pencil } from "lucide-react";
import { motion } from "motion/react";

import { Button } from "@/components/ui/button";
import type { GenerateError, DeckEntry } from "@/types";

export function ResultsGrid({
  deck,
  errors,
  busyZip,
  onEdit,
  onDownloadAll,
  onClear,
}: {
  deck: DeckEntry[];
  errors: GenerateError[];
  busyZip: boolean;
  onEdit: (index: number) => void;
  onDownloadAll: () => void;
  onClear: () => void;
}) {
  if (!deck.length && !errors.length) return null;

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">Paso 3 de 3</p>
          <h2 className="mt-1 font-serif text-3xl tracking-tight text-foreground">
            Resultado ({deck.length} carta{deck.length === 1 ? "" : "s"})
          </h2>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={onClear}>
            Vaciar
          </Button>
          <Button size="sm" onClick={onDownloadAll} disabled={!deck.length || busyZip}>
            <Download className="h-4 w-4" />
            {busyZip ? "Comprimiendo…" : "Descargar todas (ZIP)"}
          </Button>
        </div>
      </div>

      {errors.length > 0 && (
        <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-4">
          <h3 className="text-sm font-semibold text-destructive">Errores</h3>
          <ul className="mt-1 list-inside list-disc text-xs text-destructive/90">
            {errors.map((err) => (
              <li key={err.code}>
                <span className="font-mono">{err.code}</span>: {err.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        {deck.map((entry, index) => (
          <motion.article
            key={entry.id}
            layout
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col overflow-hidden rounded-xl border border-border bg-card"
          >
            <img
              src={`data:image/png;base64,${entry.png_b64}`}
              alt={entry.name}
              className="checker block w-full"
            />
            <div className="flex items-center justify-between gap-3 px-4 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-foreground">{entry.name}</p>
                <p className="font-mono text-xs text-muted-foreground">
                  {entry.code} · {entry.qty}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => onEdit(index)}>
                  <Pencil className="h-4 w-4" />
                  Editar
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <a
                    href={`data:image/png;base64,${entry.png_b64}`}
                    download={`${entry.code}.png`}
                  >
                    <Download className="h-4 w-4" />
                    Descargar
                  </a>
                </Button>
              </div>
            </div>
          </motion.article>
        ))}
      </div>
    </section>
  );
}