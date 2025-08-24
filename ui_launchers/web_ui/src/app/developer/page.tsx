import { Metadata } from "next";
import KariDevStudio from "@/components/developer/KariDevStudio";

export const metadata: Metadata = {
  title: "Kari Dev Studio",
  description: "AI-powered development environment for Kari components",
};

export default function DeveloperPage() {
  return <KariDevStudio />;
}