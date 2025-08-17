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

  return (
    <div className="flex gap-2">
      <Button size="sm" onClick={() => exec("start")}>Start</Button>
      <Button size="sm" onClick={() => exec("stop")}>Stop</Button>
      <Button size="sm" onClick={() => exec("restart")}>Restart</Button>
      <AlertDialog open={action === "delete"} onOpenChange={(o) => !o && setAction(null)}>
        <AlertDialogTrigger asChild>
          <Button size="sm" variant="destructive" onClick={() => setAction("delete")}>Delete</Button>
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
