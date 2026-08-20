import type { CSSProperties } from "react";

import { cn } from "@/lib/utils";
import { bgStyle, colorVars, type CardData } from "./types";

export interface LeaderProps extends CardData {
  className?: string;
  style?: CSSProperties;
}

export function Leader({ name, imageSrc, colors, bgPosition, bgSize, className, style }: LeaderProps) {
  return (
    <div className={cn("leader-card", className)} style={{ ...colorVars(colors), ...style }}>
      <div className="leader-text">
        <h1 className="name">{name}</h1>
      </div>
      <div
        className="leader-image character"
        role="img"
        aria-label={name}
        style={bgStyle({ imageSrc, bgPosition, bgSize })}
      />
    </div>
  );
}