import * as React from "react"
import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"
import { Button, IconButton, LinkButton, SubmitButton } from "../button"

describe("Button Polymorphic Component", () => {
  it("should render as button by default", () => {
    render(<button data-testid="button" aria-label="Button">Default button</Button>)
    
    const button = screen.getByTestId("button")
    expect(button.tagName).toBe("BUTTON")
    expect(button).toHaveTextContent("Default button")
  })

  it("should render as different elements when as prop is provided", () => {
    render(
      <div>
        <button as="a" href="#" data-testid="link-button" aria-label="Button">Link button</Button>
        <button as="div" data-testid="div-button" aria-label="Button">Div button</Button>
      </div>
    )
    
    expect(screen.getByTestId("link-button").tagName).toBe("A")
    expect(screen.getByTestId("div-button").tagName).toBe("DIV")
  })

  it("should apply variant styles correctly", () => {
    render(
      <div>
        <button variant="default" data-testid="default" aria-label="Button">Default</Button>
        <button variant="destructive" data-testid="destructive" aria-label="Button">Destructive</Button>
        <button variant="outline" data-testid="outline" aria-label="Button">Outline</Button>
        <button variant="ghost" data-testid="ghost" aria-label="Button">Ghost</Button>
      </div>
    )
    
    expect(screen.getByTestId("default")).toHaveClass("bg-primary")
    expect(screen.getByTestId("destructive")).toHaveClass("bg-destructive")
    expect(screen.getByTestId("outline")).toHaveClass("border", "border-input")
    expect(screen.getByTestId("ghost")).toHaveClass("hover:bg-accent")
  })

  it("should apply size styles correctly", () => {
    render(
      <div>
        <button size="xs" data-testid="xs" aria-label="Button">Extra small</Button>
        <button size="sm" data-testid="sm" aria-label="Button">Small</Button>
        <button size="lg" data-testid="lg" aria-label="Button">Large</Button>
        <button size="xl" data-testid="xl" aria-label="Button">Extra large</Button>
      </div>
    )
    
    expect(screen.getByTestId("xs")).toHaveClass("h-7")
    expect(screen.getByTestId("sm")).toHaveClass("h-8")
    expect(screen.getByTestId("lg")).toHaveClass("h-11")
    expect(screen.getByTestId("xl")).toHaveClass("h-12")
  })

  it("should show loading spinner when loading prop is true", () => {
    render(<button loading data-testid="loading-button" aria-label="Button">Loading</Button>)
    
    const button = screen.getByTestId("loading-button")
    expect(button).toHaveClass("cursor-not-allowed")
    expect(button.querySelector("svg")).toBeInTheDocument()
    expect(button.querySelector(".animate-spin")).toBeInTheDocument()
  })

  it("should be disabled when disabled or loading", () => {
    render(
      <div>
        <button disabled data-testid="disabled" aria-label="Button">Disabled</Button>
        <button loading data-testid="loading" aria-label="Button">Loading</Button>
      </div>
    )
    
    expect(screen.getByTestId("disabled")).toBeDisabled()
    expect(screen.getByTestId("loading")).toBeDisabled()
  })

  it("should apply fullWidth styles correctly", () => {
    render(<button fullWidth data-testid="full-width" aria-label="Button">Full width</Button>)
    
    expect(screen.getByTestId("full-width")).toHaveClass("w-full")
  })

  it("should handle click events", () => {
    const handleClick = vi.fn()
    render(<button onClick={handleClick} data-testid="clickable" aria-label="Button">Click me</Button>)
    
    fireEvent.click(screen.getByTestId("clickable"))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it("should use Slot when asChild is true", () => {
    render(
      <button asChild data-testid="as-child" aria-label="Button">
        <a href="#">Link as button</a>
      </Button>
    )
    
    const element = screen.getByTestId("as-child")
    expect(element.tagName).toBe("A")
    expect(element).toHaveAttribute("href", "#")
  })
})

describe("Predefined Button Components", () => {
  it("should render IconButton with proper dimensions", () => {
    const icon = <span data-testid="icon">🔥</span>
    render(
      <IconButton 
        icon={icon} 
        aria-label="Fire icon"
        data-testid="icon-button"
      >
        Fire
      </IconButton>
    )
    
    const button = screen.getByTestId("icon-button")
    expect(button).toHaveClass("aspect-square", "p-0", "h-10", "w-10")
    expect(screen.getByTestId("icon")).toBeInTheDocument()
    expect(screen.getByText("Fire")).toHaveClass("sr-only")
  })

  it("should render LinkButton as anchor with link variant", () => {
    render(
      <LinkButton href="/test" data-testid="link-button">
        Link button
      </LinkButton>
    )
    
    const button = screen.getByTestId("link-button")
    expect(button.tagName).toBe("A")
    expect(button).toHaveAttribute("href", "/test")
    expect(button).toHaveClass("text-primary", "underline-offset-4")
  })

  it("should render SubmitButton with submit type", () => {
    render(<SubmitButton data-testid="submit-button">Submit</SubmitButton>)
    
    const button = screen.getByTestId("submit-button")
    expect(button).toHaveAttribute("type", "submit")
    expect(button).toHaveClass("bg-primary")
  })
})