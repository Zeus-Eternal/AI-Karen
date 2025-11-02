import * as React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Text, Heading, Paragraph, Label, Caption, Code } from "../text";
describe("Text Polymorphic Component", () => {
  it("should render as span by default", () => {
    render(<Text data-testid="text">Default text</Text>)
    
    const text = screen.getByTestId("text")
    expect(text.tagName).toBe("SPAN")
    expect(text).toHaveTextContent("Default text")
  })

  it("should render as different elements when as prop is provided", () => {
    render(
      <div>
        <Text as="p" data-testid="paragraph">Paragraph text</Text>
        <Text as="h1" data-testid="heading">Heading text</Text>
        <Text as="div" data-testid="div">Div text</Text>
      </div>
    )
    
    expect(screen.getByTestId("paragraph").tagName).toBe("P")
    expect(screen.getByTestId("heading").tagName).toBe("H1")
    expect(screen.getByTestId("div").tagName).toBe("DIV")
  })

  it("should apply variant styles correctly", () => {
    render(
      <div>
        <Text variant="muted" data-testid="muted">Muted text</Text>
        <Text variant="destructive" data-testid="destructive">Destructive text</Text>
        <Text variant="success" data-testid="success">Success text</Text>
      </div>
    )
    
    expect(screen.getByTestId("muted")).toHaveClass("text-muted-foreground")
    expect(screen.getByTestId("destructive")).toHaveClass("text-destructive")
    expect(screen.getByTestId("success")).toHaveClass("text-green-600")
  })

  it("should apply size styles correctly", () => {
    render(
      <div>
        <Text size="xs" data-testid="xs">Extra small</Text>
        <Text size="lg" data-testid="lg">Large</Text>
        <Text size="2xl" data-testid="2xl">Extra large</Text>
      </div>
    )
    
    expect(screen.getByTestId("xs")).toHaveClass("text-xs")
    expect(screen.getByTestId("lg")).toHaveClass("text-lg")
    expect(screen.getByTestId("2xl")).toHaveClass("text-2xl")
  })

  it("should apply weight styles correctly", () => {
    render(
      <div>
        <Text weight="medium" data-testid="medium">Medium weight</Text>
        <Text weight="bold" data-testid="bold">Bold weight</Text>
      </div>
    )
    
    expect(screen.getByTestId("medium")).toHaveClass("font-medium")
    expect(screen.getByTestId("bold")).toHaveClass("font-bold")
  })

  it("should apply alignment styles correctly", () => {
    render(
      <div>
        <Text align="center" data-testid="center">Centered</Text>
        <Text align="right" data-testid="right">Right aligned</Text>
      </div>
    )
    
    expect(screen.getByTestId("center")).toHaveClass("text-center")
    expect(screen.getByTestId("right")).toHaveClass("text-right")
  })

  it("should apply additional styles correctly", () => {
    render(
      <div>
        <Text truncate data-testid="truncate">Truncated text</Text>
        <Text italic data-testid="italic">Italic text</Text>
        <Text underline data-testid="underline">Underlined text</Text>
      </div>
    )
    
    expect(screen.getByTestId("truncate")).toHaveClass("truncate")
    expect(screen.getByTestId("italic")).toHaveClass("italic")
    expect(screen.getByTestId("underline")).toHaveClass("underline")
  })
})

describe("Predefined Text Components", () => {
  it("should render Heading as h1 by default", () => {
    render(<Heading data-testid="heading">Heading text</Heading>)
    
    const heading = screen.getByTestId("heading")
    expect(heading.tagName).toBe("H1")
    expect(heading).toHaveClass("text-2xl", "font-bold")
  })

  it("should render Paragraph as p element", () => {
    render(<Paragraph data-testid="paragraph">Paragraph text</Paragraph>)
    
    const paragraph = screen.getByTestId("paragraph")
    expect(paragraph.tagName).toBe("P")
    expect(paragraph).toHaveClass("text-base")
  })

  it("should render Label as label element", () => {
    render(<Label data-testid="label">Label text</Label>)
    
    const label = screen.getByTestId("label")
    expect(label.tagName).toBe("LABEL")
    expect(label).toHaveClass("text-sm", "font-medium")
  })

  it("should render Caption with muted variant", () => {
    render(<Caption data-testid="caption">Caption text</Caption>)
    
    const caption = screen.getByTestId("caption")
    expect(caption).toHaveClass("text-xs", "text-muted-foreground")
  })

  it("should render Code with monospace styling", () => {
    render(<Code data-testid="code">Code text</Code>)
    
    const code = screen.getByTestId("code")
    expect(code.tagName).toBe("CODE")
    expect(code).toHaveClass("font-mono", "bg-muted")
  })
})