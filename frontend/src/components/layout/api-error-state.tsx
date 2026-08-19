import { AlertCircle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ApiError } from "@/lib/api";

/** Every failed read shows words, never a blank pane. */
export function ApiErrorState({ error, what }: { error: unknown; what: string }) {
  const message = error instanceof Error ? error.message : String(error);
  const status = error instanceof ApiError && error.status ? ` (HTTP ${error.status})` : "";
  return (
    <Alert variant="destructive" role="alert">
      <AlertCircle aria-hidden="true" />
      <AlertTitle>Could not load {what}</AlertTitle>
      <AlertDescription>
        {message}
        {status}. Nothing is shown rather than something unverified.
      </AlertDescription>
    </Alert>
  );
}
