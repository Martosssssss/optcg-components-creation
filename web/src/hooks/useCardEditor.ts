import { useEffect, useMemo, useRef, useState } from "react";

import * as api from "@/api";
import type { DeckPatch } from "@/hooks/useDeck";
import { DEFAULT_BG, bgToPositionSize, normalizeQty, readFileAsDataURL } from "@/lib/helpers";
import type { CardData } from "@/cards/types";
import type { DeckEntry } from "@/types";

const CODE_RE = /^[A-Za-z0-9-]{1,16}$/;

export function useCardEditor(
  entry: DeckEntry | null,
  index: number,
  onApply: (index: number, patch: DeckPatch) => void,
  onOpenChange: (open: boolean) => void
) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [qty, setQty] = useState("");
  const [useColors, setUseColors] = useState(true);
  const [twoColors, setTwoColors] = useState(true);
  const [color1, setColor1] = useState("#C8102E");
  const [color2, setColor2] = useState("#0057B8");
  const [zoom, setZoom] = useState(DEFAULT_BG.zoom);
  const [posX, setPosX] = useState(DEFAULT_BG.x);
  const [posY, setPosY] = useState(DEFAULT_BG.y);
  const [uploaded, setUploaded] = useState<string | null>(null);
  const [art, setArt] = useState<string | null>(null);
  const [previewPng, setPreviewPng] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const open = Boolean(entry);
  const isCard = entry?.component === "card";

  useEffect(() => {
    if (!entry) return;
    setName(entry.name);
    setCode(entry.code);
    setQty(entry.qty);
    setUseColors((entry.colors?.length ?? 0) > 0);
    setTwoColors((entry.colors?.length ?? 0) > 1);
    setColor1(entry.colors?.[0] ?? "#C8102E");
    setColor2(entry.colors?.[1] ?? "#0057B8");
    setZoom(entry.bg?.zoom ?? DEFAULT_BG.zoom);
    setPosX(entry.bg?.x ?? DEFAULT_BG.x);
    setPosY(entry.bg?.y ?? DEFAULT_BG.y);
    setUploaded(null);
    setPreviewPng(null);
    setStatus("");
    if (entry.art_b64) {
      setArt(entry.art_b64);
    } else {
      setArt(null);
      api
        .getArt(entry.code)
        .then((b64) => {
          if (b64) setArt(b64);
          else setStatus("Sin arte original en caché; sube una imagen.");
        })
        .catch(() => setStatus("No se pudo recuperar el arte original; sube una imagen."));
    }
  }, [entry?.id]);

  const colors = useMemo(() => {
    if (!useColors) return [];
    return isCard || !twoColors ? [color1] : [color1, color2];
  }, [useColors, isCard, twoColors, color1, color2]);

  const imageSrc = uploaded ?? art ?? "";
  const { position, size } = bgToPositionSize({ zoom, x: posX, y: posY });

  const cardData: CardData = {
    name: name || "Nombre",
    code,
    quantity: qty,
    imageSrc,
    colors,
    bgPosition: position,
    bgSize: size,
  };

  const edit = () => {
    setPreviewPng(null);
    setStatus("");
  };

  const handleFile = (file?: File | null) => {
    if (!file) return;
    readFileAsDataURL(file)
      .then((url) => {
        setUploaded(url);
        setPreviewPng(null);
      })
      .catch(() => setStatus("No se pudo leer la imagen."));
  };

  const handleResetImage = () => {
    setUploaded(null);
    setPreviewPng(null);
    setStatus("Usando el arte original.");
  };

  const doRender = async (busyText: string): Promise<string | null> => {
    if (!entry) return null;
    const image = uploaded ?? art;
    if (!image) {
      setStatus("Sube una imagen para poder renderizar.");
      return null;
    }
    setBusy(true);
    setStatus(busyText);
    try {
      return await api.render({
        component: entry.component,
        name: name || "Nombre",
        code: code.trim().toUpperCase() || entry.code,
        quantity: qty.trim() || entry.qty,
        colors,
        image,
        bg: { position, size },
      });
    } catch (err) {
      setStatus(`Error: ${err instanceof Error ? err.message : String(err)}`);
      return null;
    } finally {
      setBusy(false);
    }
  };

  const handlePreview = async () => {
    const png = await doRender("Previsualizando…");
    if (png) {
      setPreviewPng(png);
      setStatus("Listo.");
    }
  };

  const handleApply = async () => {
    const trimmedName = name.trim();
    if (!trimmedName) {
      setStatus("El nombre no puede estar vacío.");
      return;
    }
    const trimmedCode = code.trim().toUpperCase();
    if (!CODE_RE.test(trimmedCode)) {
      setStatus("Código no válido (solo letras, números y guiones).");
      return;
    }
    const trimmedQty = normalizeQty(qty);

    const png = await doRender("Renderizando…");
    if (!png) return;
    onApply(index, {
      name: trimmedName,
      code: trimmedCode,
      qty: trimmedQty || entry?.qty || "",
      colors,
      bg: { zoom, x: posX, y: posY },
      png_b64: png,
      art_b64: uploaded ?? undefined,
    });
    onOpenChange(false);
  };

  return {
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
  };
}