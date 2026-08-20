import type { BgState } from "@/types";

export const DEFAULT_BG: BgState = { zoom: 125, x: 50, y: 12 };

export function bgToPositionSize(bg: BgState): { position: string; size: string } {
  return {
    position: `${bg.x === 50 ? "center" : `${bg.x}%`} ${bg.y}%`,
    size: `${bg.zoom}% auto`,
  };
}

export function normalizeQty(qty: string): string {
  const trimmed = qty.trim();
  if (!trimmed) return "";
  return trimmed.startsWith("x") ? trimmed : `x${trimmed}`;
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

export function readFileAsDataURL(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}