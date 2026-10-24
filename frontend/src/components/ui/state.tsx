import { AlertCircle, Inbox, LoaderCircle, RefreshCw } from "lucide-react";
import { Button } from "./button";

export function LoadingState({ label = "Loading records" }: { label?: string }) {
  return (
    <div className="grid min-h-48 place-items-center text-sm text-muted" role="status">
      <span className="flex items-center gap-2"><LoaderCircle className="size-4 animate-spin text-teal" />{label}</span>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="grid min-h-48 place-items-center rounded-lg border border-rose-400/20 bg-rose-400/5 p-6 text-center">
      <div><AlertCircle className="mx-auto mb-3 size-5 text-rose-400" /><p className="text-sm text-rose-100">{message}</p>
        {onRetry && <Button variant="secondary" size="sm" className="mt-4" onClick={onRetry}><RefreshCw className="size-3.5" />Retry</Button>}
      </div>
    </div>
  );
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="grid min-h-48 place-items-center rounded-lg border border-dashed border-line p-6 text-center"><div><Inbox className="mx-auto mb-3 size-5 text-muted" /><p className="text-sm font-semibold">{title}</p><p className="mt-1 text-xs text-muted">{detail}</p></div></div>;
}