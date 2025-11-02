import React from 'react';
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SidebarProvider, Sidebar, SidebarMenu, SidebarMenuItem, SidebarMenuButton } from "../sidebar";

test("sidebar menu button is keyboard accessible", async () => {
  render(
    <SidebarProvider defaultOpen>
      <Sidebar>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton>Home</SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </Sidebar>
    </SidebarProvider>
  );
  const button = screen.getByRole("menuitem", { name: /home/i });
  await userEvent.tab();
  expect(button).toHaveFocus();
  await userEvent.keyboard("{Enter}");
