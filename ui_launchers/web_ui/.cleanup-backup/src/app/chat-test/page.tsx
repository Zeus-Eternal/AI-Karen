import { notFound } from "next/navigation";

export default function ChatTestPage() {
  notFound();
  return null; // This line won't be reached, but satisfies TypeScript
}
