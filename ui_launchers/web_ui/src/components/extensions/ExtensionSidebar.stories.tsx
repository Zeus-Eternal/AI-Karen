import type { Meta, StoryObj } from "@storybook/react";
import ExtensionSidebar from "./ExtensionSidebar";
import type { ExtensionSidebarProps } from "./ExtensionSidebar";

const meta: Meta<typeof ExtensionSidebar> = {
  title: "Extensions/ExtensionSidebar",
  component: ExtensionSidebar,
};
export default meta;

type Story = StoryObj<typeof ExtensionSidebar>;

export const Default: Story = {
  render: (args: ExtensionSidebarProps) => (
    <ExtensionSidebar {...args} />
  ),
  args: {
    initialCategory: "Plugins",
  },
};
