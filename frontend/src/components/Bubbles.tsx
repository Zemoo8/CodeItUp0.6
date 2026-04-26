import { useEffect, useState } from "react";

interface Bubble {
  id: number;
  size: number;
  left: number;
  duration: number;
  delay: number;
}

function makeBubbles(): Bubble[] {
  return Array.from({ length: 18 }).map((_, i) => {
    const size = 14 + Math.random() * 64;
    return {
      id: i,
      size,
      left: Math.random() * 100,
      duration: 8 + Math.random() * 12,
      delay: Math.random() * 10,
    };
  });
}

export function Bubbles() {
  const [bubbles, setBubbles] = useState<Bubble[] | null>(null);

  useEffect(() => {
    setBubbles(makeBubbles());
  }, []);

  if (!bubbles) return null;

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {bubbles.map((b) => (
        <span
          key={b.id}
          className="bubble"
          style={{
            left: `${b.left}%`,
            width: b.size,
            height: b.size,
            animationDuration: `${b.duration}s`,
            animationDelay: `${b.delay}s`,
          }}
        />
      ))}
    </div>
  );
}
