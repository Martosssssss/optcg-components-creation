import type { CSSProperties } from "react";

import { cn } from "@/lib/utils";
import { bgStyle, colorVars, type CardData } from "./types";

export interface CardProps extends CardData {
  className?: string;
  style?: CSSProperties;
}

export function Card({ name, code, quantity, imageSrc, colors, bgPosition, bgSize, className, style }: CardProps) {
  return (
    <div className={cn("card", className)} style={{ ...colorVars(colors), ...style }}>
      <div className="card-content">
        <div className="info">
          <h1 className="name">{name}</h1>
          <div className="code">{code ?? ""}</div>
        </div>
        <div
          className="character"
          role="img"
          aria-label={name}
          style={bgStyle({ imageSrc, bgPosition, bgSize })}
        />
      </div>
      <div className="quantity">{quantity ?? ""}</div>
    </div>
  );
}