import * as React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Card } from "../card";
describe("Card Compound Component", () => {
  it("should render card with all compound parts", () => {
    render(
      <Card.Root data-testid="card-root">
        <Card.Header>
          <Card.Title>Test Card Title</Card.Title>
          <Card.Description>Test card description</Card.Description>
        </Card.Header>
        <Card.Content>
          <p>Card content goes here</p>
        </Card.Content>
        <Card.Footer>
          <Card.Actions>
            <button aria-label="Button">Action 1</button>
            <button aria-label="Button">Action 2</button>
          </Card.Actions>
        </Card.Footer>
      </Card.Root>
    )

    expect(screen.getByTestId("card-root")).toBeInTheDocument()
    expect(screen.getByText("Test Card Title")).toBeInTheDocument()
    expect(screen.getByText("Test card description")).toBeInTheDocument()
    expect(screen.getByText("Card content goes here")).toBeInTheDocument()
    expect(screen.getByText("Action 1")).toBeInTheDocument()
    expect(screen.getByText("Action 2")).toBeInTheDocument()
  })

  it("should apply interactive styles when interactive prop is true", () => {
    render(
      <Card.Root interactive data-testid="interactive-card">
        <Card.Content>Interactive card</Card.Content>
      </Card.Root>
    )

    const card = screen.getByTestId("interactive-card")
    expect(card).toHaveClass("cursor-pointer")
    expect(card).toHaveClass("hover:shadow-md")
  })

  it("should apply variant styles correctly", () => {
    render(
      <Card.Root variant="elevated" data-testid="elevated-card">
        <Card.Content>Elevated card</Card.Content>
      </Card.Root>
    )

    const card = screen.getByTestId("elevated-card")
    expect(card).toHaveClass("modern-card-elevated")
  })

  it("should render card title as h3 element", () => {
    render(
      <Card.Root>
        <Card.Header>
          <Card.Title>Semantic Title</Card.Title>
        </Card.Header>
      </Card.Root>
    )

    const title = screen.getByText("Semantic Title")
    expect(title.tagName).toBe("H3")
  })

  it("should render card description as p element", () => {
    render(
      <Card.Root>
        <Card.Header>
          <Card.Description>Semantic description</Card.Description>
        </Card.Header>
      </Card.Root>
    )

    const description = screen.getByText("Semantic description")
    expect(description.tagName).toBe("P")
  })

  it("should apply justify prop to actions correctly", () => {
    render(
      <Card.Root>
        <Card.Actions justify="center" data-testid="centered-actions">
          <button aria-label="Button">Centered Action</button>
        </Card.Actions>
      </Card.Root>
    )

    const actions = screen.getByTestId("centered-actions")
    expect(actions).toHaveClass("justify-center")
  })
})