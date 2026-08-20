import type { CSSProperties } from "react";

export interface CardData {
  name: string;
  code?: string;
  quantity?: string;
  imageSrc: string;
  colors?: string[];
  bgPosition?: string;
  bgSize?: string;
}

export const DEFAULT_BG = {
  position: "center 12%",
  size: "125% auto",
};

export function bgStyle(data: Pick<CardData, "imageSrc" | "bgPosition" | "bgSize">) {
  const style: CSSProperties = {
    backgroundRepeat: "no-repeat",
    backgroundPosition: data.bgPosition ?? DEFAULT_BG.position,
    backgroundSize: data.bgSize ?? DEFAULT_BG.size,
  };
  if (data.imageSrc) style.backgroundImage = `url("${data.imageSrc}")`;
  return style;
}

export function colorVars(colors?: string[]) {
  if (!colors || !colors.length) return undefined;
  return {
    "--optcg-c1": colors[0],
    "--optcg-c2": colors[1] ?? colors[0],
  } as CSSProperties;
}