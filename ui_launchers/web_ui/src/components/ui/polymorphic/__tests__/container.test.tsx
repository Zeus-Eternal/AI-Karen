import * as React from "react"
import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { Container, FlexContainer, GridContainer, CenteredContainer } from "../container"

describe("Container Polymorphic Component", () => {
  it("should render as div by default", () => {
    render(<Container data-testid="container">Default container</Container>)
    
    const container = screen.getByTestId("container")
    expect(container.tagName).toBe("DIV")
    expect(container).toHaveTextContent("Default container")
  })

  it("should render as different elements when as prop is provided", () => {
    render(
      <div>
        <Container as="section" data-testid="section">Section container</Container>
        <Container as="article" data-testid="article">Article container</Container>
        <Container as="main" data-testid="main">Main container</Container>
      </div>
    )
    
    expect(screen.getByTestId("section").tagName).toBe("SECTION")
    expect(screen.getByTestId("article").tagName).toBe("ARTICLE")
    expect(screen.getByTestId("main").tagName).toBe("MAIN")
  })

  it("should apply display styles correctly", () => {
    render(
      <div>
        <Container display="flex" data-testid="flex">Flex container</Container>
        <Container display="grid" data-testid="grid">Grid container</Container>
        <Container display="inline-flex" data-testid="inline-flex">Inline flex</Container>
      </div>
    )
    
    expect(screen.getByTestId("flex")).toHaveClass("flex")
    expect(screen.getByTestId("grid")).toHaveClass("grid")
    expect(screen.getByTestId("inline-flex")).toHaveClass("inline-flex")
  })

  it("should apply variant styles correctly", () => {
    render(
      <div>
        <Container variant="default" data-testid="default">Default</Container>
        <Container variant="centered" data-testid="centered">Centered</Container>
        <Container variant="padded" data-testid="padded">Padded</Container>
        <Container variant="fluid" data-testid="fluid">Fluid</Container>
      </div>
    )
    
    expect(screen.getByTestId("default")).toHaveClass("mx-auto", "w-full", "px-4")
    expect(screen.getByTestId("centered")).toHaveClass("mx-auto", "flex", "items-center", "justify-center")
    expect(screen.getByTestId("padded")).toHaveClass("px-4")
    expect(screen.getByTestId("fluid")).toHaveClass("w-full")
  })

  it("should apply responsive size styles correctly", () => {
    render(
      <div>
        <Container size="sm" data-testid="sm">Small</Container>
        <Container size="lg" data-testid="lg">Large</Container>
        <Container size="2xl" data-testid="2xl">Extra large</Container>
      </div>
    )
    
    expect(screen.getByTestId("sm")).toHaveClass("max-w-sm")
    expect(screen.getByTestId("lg")).toHaveClass("max-w-lg")
    expect(screen.getByTestId("2xl")).toHaveClass("max-w-2xl")
  })

  it("should apply non-responsive size styles when responsive is false", () => {
    render(
      <div>
        <Container size="sm" responsive={false} data-testid="non-responsive-sm">Small</Container>
        <Container size="lg" responsive={false} data-testid="non-responsive-lg">Large</Container>
      </div>
    )
    
    expect(screen.getByTestId("non-responsive-sm")).toHaveClass("w-96")
    expect(screen.getByTestId("non-responsive-lg")).toHaveClass("w-[40rem]")
  })
})

describe("FlexContainer Component", () => {
  it("should render with flex display and apply flex properties", () => {
    render(
      <FlexContainer 
        direction="column"
        align="center"
        justify="between"
        wrap
        gap="md"
        data-testid="flex-container"
      >
        <div>Item 1</div>
        <div>Item 2</div>
      </FlexContainer>
    )
    
    const container = screen.getByTestId("flex-container")
    expect(container).toHaveClass(
      "flex",
      "flex-col",
      "items-center", 
      "justify-between",
      "flex-wrap",
      "gap-4"
    )
  })

  it("should apply different flex directions", () => {
    render(
      <div>
        <FlexContainer direction="row" data-testid="row">Row</FlexContainer>
        <FlexContainer direction="column" data-testid="column">Column</FlexContainer>
        <FlexContainer direction="row-reverse" data-testid="row-reverse">Row reverse</FlexContainer>
      </div>
    )
    
    expect(screen.getByTestId("row")).toHaveClass("flex-row")
    expect(screen.getByTestId("column")).toHaveClass("flex-col")
    expect(screen.getByTestId("row-reverse")).toHaveClass("flex-row-reverse")
  })

  it("should apply different gap sizes", () => {
    render(
      <div>
        <FlexContainer gap="xs" data-testid="xs-gap">XS Gap</FlexContainer>
        <FlexContainer gap="lg" data-testid="lg-gap">LG Gap</FlexContainer>
        <FlexContainer gap="xl" data-testid="xl-gap">XL Gap</FlexContainer>
      </div>
    )
    
    expect(screen.getByTestId("xs-gap")).toHaveClass("gap-1")
    expect(screen.getByTestId("lg-gap")).toHaveClass("gap-6")
    expect(screen.getByTestId("xl-gap")).toHaveClass("gap-8")
  })
})

describe("GridContainer Component", () => {
  it("should render with grid display and apply grid properties", () => {
    render(
      <GridContainer 
        columns={3}
        gap="lg"
        data-testid="grid-container"
      >
        <div>Item 1</div>
        <div>Item 2</div>
        <div>Item 3</div>
      </GridContainer>
    )
    
    const container = screen.getByTestId("grid-container")
    expect(container).toHaveClass("grid", "gap-6")
    expect(container).toHaveStyle({ gridTemplateColumns: "repeat(3, 1fr)" })
  })

  it("should apply auto-fit when autoFit is true", () => {
    render(
      <GridContainer 
        autoFit
        minItemWidth="200px"
        data-testid="auto-fit-grid"
      >
        <div>Item 1</div>
        <div>Item 2</div>
      </GridContainer>
    )
    
    const container = screen.getByTestId("auto-fit-grid")
    expect(container).toHaveStyle({ 
      gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" 
    })
  })
})

describe("Predefined Container Components", () => {
  it("should render CenteredContainer with centered variant", () => {
    render(<CenteredContainer data-testid="centered">Centered</CenteredContainer>)
    
    const container = screen.getByTestId("centered")
    expect(container).toHaveClass("mx-auto", "flex", "items-center", "justify-center")
  })
})