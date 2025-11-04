import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Button, IconButton, LinkButton, SubmitButton } from "../button";
describe("Button Polymorphic Component", () => {
  it("should render as button by default", () => {
    render(<Button data-testid="button" >Default button</Button>)
    
    const button = screen.getByTestId("button")
    expect(button.tagName).toBe("BUTTON")
    expect(button).toHaveTextContent("Default button")
  })

  it("should render as different elements when as prop is provided", () => {
    render(
      <div>
        <Button as="a" href="#" data-testid="link-button" >Link button</Button>
        <Button as="div" data-testid="div-button" >Div button</Button>
      </div>
    )
    
    expect(screen.getByTestId("link-button").tagName).toBe("A")
    expect(screen.getByTestId("div-button").tagName).toBe("DIV")
  })

  it("should apply variant styles correctly", () => {
    render(
      <div>
        <Button variant="default" data-testid="default" >Default</Button>
        <Button variant="destructive" data-testid="destructive" >Destructive</Button>
        <Button variant="outline" data-testid="outline" >Outline</Button>
        <Button variant="ghost" data-testid="ghost" >Ghost</Button>
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
        <Button size="xs" data-testid="xs" >Extra small</Button>
        <Button size="sm" data-testid="sm" >Small</Button>
        <Button size="lg" data-testid="lg" >Large</Button>
        <Button size="xl" data-testid="xl" >Extra large</Button>
      </div>
    )
    
    expect(screen.getByTestId("xs")).toHaveClass("h-7")
    expect(screen.getByTestId("sm")).toHaveClass("h-8")
    expect(screen.getByTestId("lg")).toHaveClass("h-11")
    expect(screen.getByTestId("xl")).toHaveClass("h-12")
  })

  it("should show loading spinner when loading prop is true", () => {
    render(<Button loading data-testid="loading-button" >Loading</Button>)
    
    const button = screen.getByTestId("loading-button")
    expect(button).toHaveClass("cursor-not-allowed")
    expect(button.querySelector("svg")).toBeInTheDocument()
    expect(button.querySelector(".animate-spin")).toBeInTheDocument()
  })

  it("should be disabled when disabled or loading", () => {
    render(
      <div>
        <Button disabled data-testid="disabled" >Disabled</Button>
        <Button loading data-testid="loading" >Loading</Button>
      </div>
    )
    
    expect(screen.getByTestId("disabled")).toBeDisabled()
    expect(screen.getByTestId("loading")).toBeDisabled()
  })

  it("should apply fullWidth styles correctly", () => {
    render(<Button fullWidth data-testid="full-width" >Full width</Button>)
    
    expect(screen.getByTestId("full-width")).toHaveClass("w-full")
  })

  it("should handle click events", () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick} data-testid="clickable" >Click me</Button>)
    
    fireEvent.click(screen.getByTestId("clickable"))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it("should use Slot when asChild is true", () => {
    render(
      <Button asChild data-testid="as-child" aria-label="Button">
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