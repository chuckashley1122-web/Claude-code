export function Avatar({ name, size = 28 }: { name: string; size?: number }) {
  const hue = name.split("").reduce((a, c) => a + c.charCodeAt(0), 0) % 360;
  return (
    <span
      aria-hidden
      style={{ width: size, height: size, background: `hsl(${hue} 55% 90%)`, color: `hsl(${hue} 55% 30%)` }}
      className="inline-flex shrink-0 items-center justify-center rounded-md text-xs font-semibold"
    >
      {name.slice(0, 1).toUpperCase()}
    </span>
  );
}
