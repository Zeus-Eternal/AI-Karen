import * as React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { useForm } from "react-hook-form";
import { Form } from "../form";
// Test wrapper component
const TestFormWrapper = ({ children }: { children: React.ReactNode }) => {
  const methods = useForm()
  return <Form.Root {...methods}>{children}</Form.Root>
}

describe("Form Compound Component", () => {
  it("should render form with all compound parts", () => {
    render(
      <TestFormWrapper>
        <Form.Group data-testid="form-group">
          <Form.Item>
            <Form.Label htmlFor="test-input">Test Label</Form.Label>
            <Form.Control>
              <input id="test-input" placeholder="Test input" />
            </Form.Control>
            <Form.Description>This is a test input</Form.Description>
            <Form.Error>Test error message</Form.Error>
          </Form.Item>
        </Form.Group>
        <Form.Actions>
          <button type="button" aria-label="Button">Cancel</button>
          <button type="submit" aria-label="Submit form">Submit</button>
        </Form.Actions>
      </TestFormWrapper>
    )

    expect(screen.getByTestId("form-group")).toBeInTheDocument()
    expect(screen.getByText("Test Label")).toBeInTheDocument()
    expect(screen.getByPlaceholderText("Test input")).toBeInTheDocument()
    expect(screen.getByText("This is a test input")).toBeInTheDocument()
    expect(screen.getByText("Test error message")).toBeInTheDocument()
    expect(screen.getByText("Cancel")).toBeInTheDocument()
    expect(screen.getByText("Submit")).toBeInTheDocument()
  })

  it("should render required asterisk when required prop is true", () => {
    render(
      <TestFormWrapper>
        <Form.Item>
          <Form.Label required>Required Field</Form.Label>
        </Form.Item>
      </TestFormWrapper>
    )

    expect(screen.getByText("*")).toBeInTheDocument()
  })

  it("should apply orientation classes to form group", () => {
    render(
      <TestFormWrapper>
        <Form.Group orientation="horizontal" data-testid="horizontal-group">
          <Form.Item>
            <Form.Label>Field 1</Form.Label>
          </Form.Item>
          <Form.Item>
            <Form.Label>Field 2</Form.Label>
          </Form.Item>
        </Form.Group>
      </TestFormWrapper>
    )

    const group = screen.getByTestId("horizontal-group")
    expect(group).toHaveClass("flex")
    expect(group).toHaveClass("flex-wrap")
    expect(group).toHaveClass("gap-4")
  })

  it("should apply justify prop to actions correctly", () => {
    render(
      <TestFormWrapper>
        <Form.Actions justify="center" data-testid="centered-actions">
          <button aria-label="Button">Centered Action</button>
        </Form.Actions>
      </TestFormWrapper>
    )

    const actions = screen.getByTestId("centered-actions")
    expect(actions).toHaveClass("sm:justify-center")
  })

  it("should apply sticky styles when sticky prop is true", () => {
    render(
      <TestFormWrapper>
        <Form.Actions sticky data-testid="sticky-actions">
          <button aria-label="Button">Sticky Action</button>
        </Form.Actions>
      </TestFormWrapper>
    )

    const actions = screen.getByTestId("sticky-actions")
    expect(actions).toHaveClass("sticky")
    expect(actions).toHaveClass("bottom-0")
    expect(actions).toHaveClass("bg-background")
  })

  it("should render form section with fieldset", () => {
    render(
      <TestFormWrapper>
        <Form.Section data-testid="form-section">
          <Form.Legend>Section Title</Form.Legend>
          <Form.Item>
            <Form.Label>Field in section</Form.Label>
          </Form.Item>
        </Form.Section>
      </TestFormWrapper>
    )

    const section = screen.getByTestId("form-section")
    expect(section.tagName).toBe("FIELDSET")
    expect(screen.getByText("Section Title")).toBeInTheDocument()
  })
})