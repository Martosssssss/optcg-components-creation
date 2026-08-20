import type { GenerateResponse, RenderPayload } from "./types";

const JSON_HEADERS = { "Content-Type": "application/json" };

async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (data && typeof data.error === "string") return data.error;
  } catch {
    /* cuerpo no JSON */
  }
  return `Error ${res.status}`;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function getComponents(): Promise<string[]> {
  const data = await request<{ components?: unknown }>("/api/components");
  return Array.isArray(data.components) ? (data.components as string[]) : [];
}

export async function generate(
  text: string,
  component: string
): Promise<GenerateResponse> {
  return request<GenerateResponse>("/api/generate", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ text, component }),
  });
}

export async function getArt(code: string): Promise<string | null> {
  const res = await fetch(`/api/art?code=${encodeURIComponent(code)}`);
  if (!res.ok) return null;
  const data = await res.json();
  if (typeof data.art_b64 !== "string") return null;
  const mime = data.art_b64.startsWith("iVBORw0KGgo") ? "image/png" : "image/jpeg";
  return `data:${mime};base64,${data.art_b64}`;
}

export async function render(payload: RenderPayload): Promise<string> {
  const data = await request<{ png_b64?: unknown }>("/api/render", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  });
  if (typeof data.png_b64 !== "string") throw new Error("respuesta inválida de /api/render");
  return data.png_b64;
}

export async function zip(files: { filename: string; png_b64: string }[]): Promise<Blob> {
  const res = await fetch("/api/zip", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ files }),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.blob();
}