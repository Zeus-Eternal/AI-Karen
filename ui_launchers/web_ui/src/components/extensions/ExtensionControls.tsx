"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction } from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";

export default function ExtensionControls() {
  const { toast } = useToast();
  const [action, setAction] = useState<string | null>(null);

  const exec = (act: string) => {
    setAction(null);
    toast({ title: `Action executed`, description: act });
  };

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);


  return (
    <div className="flex gap-2">
      <button size="sm" onClick={() = aria-label="Button"> exec("start")}>Start</Button>
      <button size="sm" onClick={() = aria-label="Button"> exec("stop")}>Stop</Button>
      <button size="sm" onClick={() = aria-label="Button"> exec("restart")}>Restart</Button>
      <AlertDialog open={action === "delete"} onOpenChange={(o) => !o && setAction(null)}>
        <AlertDialogTrigger asChild>
          <button size="sm" variant="destructive" onClick={() = aria-label="Button"> setAction("delete")}>Delete</Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogTitle>Confirm Delete</AlertDialogTitle>
          <AlertDialogDescription>This action cannot be undone.</AlertDialogDescription>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => exec("delete")}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
