import * as DialogPrimitive from "@radix-ui/react-dialog";
import type { ReactNode } from "react";
import { X } from "lucide-react";

export function Dialog({ open, onOpenChange, title, description, children }: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="dialog-overlay" />
      <DialogPrimitive.Content className="dialog-content">
        <header className="dialog-header"><div><DialogPrimitive.Title className="dialog-title">{title}</DialogPrimitive.Title>{description && <DialogPrimitive.Description className="dialog-description">{description}</DialogPrimitive.Description>}</div><DialogPrimitive.Close className="dialog-close" aria-label="Close dialog"><X className="size-4" /></DialogPrimitive.Close></header>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  </DialogPrimitive.Root>;
}