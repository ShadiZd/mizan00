/* Loading + error primitives shared by every feature card. */
import { RefreshCw } from "lucide-react";

export function Shimmer({ className = "" }: { className?: string }) {
  return (
    <div
      className={`relative overflow-hidden rounded-xl bg-muted/60 ${className}`}
      aria-hidden
    >
      <div className="absolute inset-0 -translate-x-full animate-[sweep_1.6s_ease-in-out_infinite] bg-gradient-to-r from-transparent via-card/70 to-transparent" />
    </div>
  );
}

export function SkeletonStack({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <Shimmer key={i} className="h-12 w-full" />
      ))}
    </div>
  );
}

export function ErrorRetry({
  message = "Couldn't load. Tap to retry.",
  onRetry,
}: {
  message?: string;
  onRetry: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onRetry}
      className="flex w-full items-center justify-center gap-2 rounded-2xl border border-destructive/30 bg-destructive/5 px-4 py-6 text-sm text-destructive transition-colors hover:bg-destructive/10"
    >
      <RefreshCw className="h-4 w-4" strokeWidth={1.8} />
      {message}
    </button>
  );
}
