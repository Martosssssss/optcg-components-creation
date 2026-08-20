import { useEffect, useRef, useState, type ReactNode } from "react";

const PREVIEW_W = 1960;
const PREVIEW_H = 367;

export function CardPreview({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0.2);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const update = () => setScale(el.clientWidth / PREVIEW_W);
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={className}
      style={{
        position: "relative",
        width: "100%",
        aspectRatio: `${PREVIEW_W} / ${PREVIEW_H}`,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: PREVIEW_W,
          height: PREVIEW_H,
          transform: `scale(${scale})`,
          transformOrigin: "top left",
        }}
      >
        <div className="card-viewport" style={{ width: PREVIEW_W, height: PREVIEW_H }}>
          {children}
        </div>
      </div>
    </div>
  );
}