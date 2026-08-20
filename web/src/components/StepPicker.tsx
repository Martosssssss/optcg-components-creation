import { motion } from "motion/react";

import { Card } from "@/cards/Card";
import { CardPreview } from "@/cards/CardPreview";
import { Leader } from "@/cards/Leader";
import { Button } from "@/components/ui/button";

const SAMPLE_IMAGE: Record<string, string> = {
  card: "/example_images/card.png",
  leader: "/example_images/leader.png",
};

export function CardComponent({ name, imageSrc }: { name: string; imageSrc: string }) {
  const human = humanize(name);
  if (name === "leader") {
    return <Leader name={human} imageSrc={imageSrc} />;
  }
  return <Card name={human} code="OP16-000" quantity="x4" imageSrc={imageSrc} />;
}

function humanize(name: string) {
  return name.replace(/[-_]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function StepPicker({ components, onSelect }: { components: string[]; onSelect: (name: string) => void }) {
  return (
    <section className="space-y-6">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">Paso 1 de 3</p>
        <h1 className="mt-1 font-serif text-4xl tracking-tight text-foreground">Elige un componente</h1>
        <p className="mt-2 max-w-xl text-sm text-muted-foreground">
          Cada componente define el diseño de la carta (información, foto y badge de cantidad).
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {components.map((name, i) => (
          <motion.article
            key={name}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05, duration: 0.3 }}
            className="flex flex-col gap-4 rounded-xl border border-border bg-card p-4"
          >
            <CardPreview className="rounded-lg border border-border">
              <CardComponent name={name} imageSrc={SAMPLE_IMAGE[name] ?? SAMPLE_IMAGE.card} />
            </CardPreview>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-foreground">{humanize(name)}</p>
              </div>
              <Button size="sm" onClick={() => onSelect(name)}>
                Usar este
              </Button>
            </div>
          </motion.article>
        ))}
      </div>
    </section>
  );
}