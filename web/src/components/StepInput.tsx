import { useRef, useState } from "react";
import { FileUp, Pencil } from "lucide-react";

import { Button } from "@/components/ui/button";
import { readFileAsText } from "@/lib/helpers";

export function StepInput({
  component,
  busy,
  onGenerate,
  onBack,
}: {
  component: string;
  busy: boolean;
  onGenerate: (text: string) => void;
  onBack: () => void;
}) {
  const [text, setText] = useState("");
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = (file?: File | null) => {
    if (!file) return;
    readFileAsText(file)
      .then(setText)
      .catch(() => setText(""));
  };

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">Paso 2 de 3</p>
          <h1 className="mt-1 font-serif text-4xl tracking-tight text-foreground">Añade las cartas</h1>
          <p className="mt-2 max-w-xl text-sm text-muted-foreground">
            Sube un <code className="rounded bg-muted px-1 font-mono text-xs">.txt</code> o pega el texto con una carta
            por línea (<code className="rounded bg-muted px-1 font-mono text-xs">cantidadxcódigo</code>, ej.{" "}
            <code className="rounded bg-muted px-1 font-mono text-xs">4xOP15-014</code>).
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onBack}>
          Cambiar componente
        </Button>
      </div>

      <div className="rounded-xl border border-border bg-card p-6">
        <div
          role="button"
          tabIndex={0}
          onClick={() => fileRef.current?.click()}
          onKeyDown={(e) => e.key === "Enter" && fileRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            handleFile(e.dataTransfer.files?.[0]);
          }}
          className={`flex cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border border-dashed p-8 text-center transition-colors ${
            dragging ? "border-foreground bg-muted" : "border-input hover:border-muted-foreground"
          }`}
        >
          <FileUp className="h-6 w-6 text-muted-foreground" />
          <p className="text-sm font-medium text-foreground">Subir archivo .txt</p>
          <p className="text-xs text-muted-foreground">o arrastra y suelta aquí</p>
          <input
            ref={fileRef}
            type="file"
            accept=".txt,text/plain"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
        </div>

        <label htmlFor="text-input" className="mt-6 mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
          <Pencil className="h-4 w-4 text-muted-foreground" />
          O pega el texto
        </label>
        <textarea
          id="text-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          spellCheck={false}
          placeholder={"4xOP15-014\n2xOP05-019"}
          className="w-full resize-y rounded-md border border-input bg-background px-3 py-2 font-mono text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />

        <div className="mt-4 flex items-center gap-3">
          <Button disabled={!text.trim() || busy} onClick={() => onGenerate(text)}>
            {busy ? "Generando…" : "Generar cartas"}
          </Button>
          <p className="text-xs text-muted-foreground">
            Componente: <span className="font-semibold text-foreground">{component}</span>
          </p>
        </div>
      </div>
    </section>
  );
}