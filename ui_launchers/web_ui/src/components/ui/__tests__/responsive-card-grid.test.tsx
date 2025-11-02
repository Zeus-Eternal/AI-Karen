import React from 'react';
import { render, screen } from "@testing-library/react";
import ResponsiveCardGrid from "../responsive-card-grid";

test("renders children in a responsive grid", () => {
  render(
    <ResponsiveCardGrid data-testid="grid">
      <div>one</div>
      <div>two</div>
    </ResponsiveCardGrid>
  );
  const grid = screen.getByTestId("grid");
  expect(grid.className).toMatch(/grid/);
