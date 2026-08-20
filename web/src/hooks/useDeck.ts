import { useState } from "react";

import { normalizeQty } from "@/lib/helpers";
import type { BgState, ComponentType, DeckEntry } from "@/types";

export interface DeckPatch {
  name: string;
  code: string;
  qty: string;
  colors: string[];
  bg: BgState;
  png_b64: string;
  art_b64?: string;
}

export function useDeck() {
  const [deck, setDeck] = useState<DeckEntry[]>([]);

  const replaceAll = (
    cards: { code: string; name: string; qty: string; colors: string[]; png_b64: string }[],
    component: string
  ) => {
    setDeck(
      cards.map((card, i) => ({
        id: i + 1,
        component: component as ComponentType,
        code: card.code,
        name: card.name,
        qty: normalizeQty(card.qty),
        colors: card.colors || [],
        art_b64: null,
        png_b64: card.png_b64,
        bg: null,
      }))
    );
  };

  const applyEdit = (index: number, patch: DeckPatch) => {
    setDeck((prev) =>
      prev.map((entry, i) =>
        i === index
          ? {
              ...entry,
              name: patch.name,
              code: patch.code,
              qty: patch.qty,
              colors: patch.colors,
              bg: patch.bg,
              png_b64: patch.png_b64,
              art_b64: patch.art_b64 ?? entry.art_b64,
            }
          : entry
      )
    );
  };

  const clear = () => setDeck([]);

  return { deck, replaceAll, applyEdit, clear };
}