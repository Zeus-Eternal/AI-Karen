import * as React from "react"
import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"
import { Modal } from "../modal"

describe("Modal Compound Component", () => {
  it("should render modal with all compound parts", () => {
    render(
      <Modal.Root open={true}>
        <Modal.Content data-testid="modal-content">
          <Modal.Header>
            <Modal.Title>Test Modal Title</Modal.Title>
            <Modal.Description>Test modal description</Modal.Description>
          </Modal.Header>
          <Modal.Body>
            <p>Modal body content</p>
          </Modal.Body>
          <Modal.Actions>
            <button>Cancel</button>
            <button>Confirm</button>
          </Modal.Actions>
        </Modal.Content>
      </Modal.Root>
    )

    expect(screen.getByTestId("modal-content")).toBeInTheDocument()
    expect(screen.getByText("Test Modal Title")).toBeInTheDocument()
    expect(screen.getByText("Test modal description")).toBeInTheDocument()
    expect(screen.getByText("Modal body content")).toBeInTheDocument()
    expect(screen.getByText("Cancel")).toBeInTheDocument()
    expect(screen.getByText("Confirm")).toBeInTheDocument()
  })

  it("should apply size classes correctly", () => {
    render(
      <Modal.Root open={true}>
        <Modal.Content size="lg" data-testid="large-modal">
          <Modal.Body>Large modal</Modal.Body>
        </Modal.Content>
      </Modal.Root>
    )

    const modal = screen.getByTestId("large-modal")
    expect(modal).toHaveClass("max-w-2xl")
  })

  it("should render close button by default", () => {
    render(
      <Modal.Root open={true}>
        <Modal.Content>
          <Modal.Body>Modal with close button</Modal.Body>
        </Modal.Content>
      </Modal.Root>
    )

    expect(screen.getByRole("button", { name: /close/i })).toBeInTheDocument()
  })

  it("should hide close button when showCloseButton is false", () => {
    render(
      <Modal.Root open={true}>
        <Modal.Content showCloseButton={false}>
          <Modal.Body>Modal without close button</Modal.Body>
        </Modal.Content>
      </Modal.Root>
    )

    expect(screen.queryByRole("button", { name: /close/i })).not.toBeInTheDocument()
  })

  it("should apply justify prop to actions correctly", () => {
    render(
      <Modal.Root open={true}>
        <Modal.Content>
          <Modal.Actions justify="center" data-testid="centered-actions">
            <button>Centered Action</button>
          </Modal.Actions>
        </Modal.Content>
      </Modal.Root>
    )

    const actions = screen.getByTestId("centered-actions")
    expect(actions).toHaveClass("sm:justify-center")
  })

  it("should render trigger component", () => {
    render(
      <Modal.Root>
        <Modal.Trigger asChild>
          <button>Open Modal</button>
        </Modal.Trigger>
        <Modal.Content>
          <Modal.Body>Modal content</Modal.Body>
        </Modal.Content>
      </Modal.Root>
    )

    expect(screen.getByText("Open Modal")).toBeInTheDocument()
  })
})