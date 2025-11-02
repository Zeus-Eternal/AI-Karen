import { ChatMessage } from "../types";
import { summarizeMessagesForExport } from "./messageUtils";

export interface ExportPayload {
  summary: ReturnType<typeof summarizeMessagesForExport>;
  messages: ChatMessage[];
}

export const buildExportPayload = (messages: ChatMessage[]): ExportPayload => ({
  summary: summarizeMessagesForExport(messages),
  messages,
});

export const toDownloadBlob = (payload: ExportPayload) =>
  new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });

export const triggerDownload = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
