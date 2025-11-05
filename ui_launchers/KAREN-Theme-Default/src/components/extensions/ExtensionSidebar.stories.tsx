import React from 'react';
import type { Meta, StoryObj } from "@storybook/react";
import ExtensionSidebar from "./ExtensionSidebar";
import type { ExtensionSidebarProps } from "./ExtensionSidebar";
import { SidebarProvider } from "@/components/ui/sidebar";

const meta: Meta<typeof ExtensionSidebar> = {
  title: "Extensions/ExtensionSidebar",
  component: ExtensionSidebar,
};
export default meta;

type Story = StoryObj<typeof ExtensionSidebar>;

export const Default: Story = {
  render: (args: ExtensionSidebarProps) => (
    <SidebarProvider>
      <ExtensionSidebar {...args} />
    </SidebarProvider>
  ),
  args: {
    initialCategory: "Plugins",
  },
};
