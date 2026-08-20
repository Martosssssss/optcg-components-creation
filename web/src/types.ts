export interface GeneratedCard {
  code: string;
  name: string;
  qty: string;
  colors: string[];
  png_b64: string;
}

export type ComponentType = "card" | "leader";

export interface GenerateError {
  code: string;
  reason: string;
}

export interface GenerateResponse {
  cards: GeneratedCard[];
  errors: GenerateError[];
}

export interface BgState {
  zoom: number;
  x: number;
  y: number;
}

export interface DeckEntry {
  id: number;
  component: ComponentType;
  code: string;
  name: string;
  qty: string;
  colors: string[];
  art_b64: string | null;
  png_b64: string;
  bg: BgState | null;
}

export interface RenderPayload {
  component: string;
  name: string;
  code: string;
  quantity: string;
  colors: string[];
  image: string;
  bg: { position: string; size: string };
}