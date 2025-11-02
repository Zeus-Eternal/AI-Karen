import { Metadata } from "next";
import { notFound } from "next/navigation";

export const metadata: Metadata = {
  title: "Page not available",
  description: "The legacy developer console is disabled in production.",
};

export default function DeveloperPage() {
  notFound();
}