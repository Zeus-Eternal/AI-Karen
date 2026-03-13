import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { 
  Card, 
  CardHeader, 
  CardFooter, 
  CardTitle, 
  CardDescription, 
  CardContent 
} from '../card';

describe('Card Components', () => {
  describe('Card', () => {
    it('renders correctly with default props', () => {
      render(<Card>Card Content</Card>);
      const card = screen.getByText('Card Content');
      expect(card).toBeInTheDocument();
      expect(card).toHaveClass('rounded-lg border bg-card text-card-foreground shadow-sm');
    });

    it('renders with custom className', () => {
      render(<Card className="custom-class">Card Content</Card>);
      const card = screen.getByText('Card Content');
      expect(card).toHaveClass('custom-class');
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(<Card ref={ref}>Card Content</Card>);
      expect(ref.current?.constructor.name).toBe('HTMLDivElement');
      expect(ref.current).toHaveTextContent('Card Content');
    });

    it('has proper display name', () => {
      expect(Card.displayName).toBe('Card');
    });

    it('supports HTML attributes', () => {
      render(
        <Card 
          data-testid="custom-card" 
          title="Card Title"
          aria-label="Card Label"
        >
          Card Content
        </Card>
      );
      const card = screen.getByTestId('custom-card');
      expect(card).toHaveAttribute('title', 'Card Title');
      expect(card).toHaveAttribute('aria-label', 'Card Label');
    });

    it('handles click events', () => {
      const handleClick = vi.fn();
      render(<Card onClick={handleClick}>Clickable Card</Card>);
      const card = screen.getByText('Clickable Card');
      card.click();
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('CardHeader', () => {
    it('renders correctly with default props', () => {
      render(
        <CardHeader>
          <CardTitle>Header Title</CardTitle>
          <CardDescription>Header Description</CardDescription>
        </CardHeader>
      );
      const header = screen.getByText('Header Title').parentElement;
      expect(header).toBeInTheDocument();
      expect(header).toHaveClass('flex flex-col space-y-1.5 p-6');
    });

    it('renders with custom className', () => {
      render(<CardHeader className="custom-class">Header Content</CardHeader>);
      const header = screen.getByText('Header Content');
      expect(header).toHaveClass('custom-class');
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(<CardHeader ref={ref}>Header Content</CardHeader>);
      expect(ref.current?.constructor.name).toBe('HTMLDivElement');
      expect(ref.current).toHaveTextContent('Header Content');
    });

    it('has proper display name', () => {
      expect(CardHeader.displayName).toBe('CardHeader');
    });
  });

  describe('CardTitle', () => {
    it('renders correctly with default props', () => {
      render(<CardTitle>Card Title</CardTitle>);
      const title = screen.getByText('Card Title');
      expect(title).toBeInTheDocument();
      expect(title.tagName).toBe('H3');
      expect(title).toHaveClass('text-2xl font-semibold leading-none tracking-tight');
    });

    it('renders with custom className', () => {
      render(<CardTitle className="custom-class">Custom Title</CardTitle>);
      const title = screen.getByText('Custom Title');
      expect(title).toHaveClass('custom-class');
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLHeadingElement>();
      render(<CardTitle ref={ref}>Title Content</CardTitle>);
      expect(ref.current?.constructor.name).toBe('HTMLHeadingElement');
      expect(ref.current).toHaveTextContent('Title Content');
    });

    it('has proper display name', () => {
      expect(CardTitle.displayName).toBe('CardTitle');
    });
  });

  describe('CardDescription', () => {
    it('renders correctly with default props', () => {
      render(<CardDescription>Card Description</CardDescription>);
      const description = screen.getByText('Card Description');
      expect(description).toBeInTheDocument();
      expect(description.tagName).toBe('P');
      expect(description).toHaveClass('text-sm text-muted-foreground');
    });

    it('renders with custom className', () => {
      render(<CardDescription className="custom-class">Custom Description</CardDescription>);
      const description = screen.getByText('Custom Description');
      expect(description).toHaveClass('custom-class');
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLParagraphElement>();
      render(<CardDescription ref={ref}>Description Content</CardDescription>);
      expect(ref.current?.constructor.name).toBe('HTMLParagraphElement');
      expect(ref.current).toHaveTextContent('Description Content');
    });

    it('has proper display name', () => {
      expect(CardDescription.displayName).toBe('CardDescription');
    });
  });

  describe('CardContent', () => {
    it('renders correctly with default props', () => {
      render(<CardContent>Card Content</CardContent>);
      const content = screen.getByText('Card Content');
      expect(content).toBeInTheDocument();
      expect(content).toHaveClass('p-6 pt-0');
    });

    it('renders with custom className', () => {
      render(<CardContent className="custom-class">Custom Content</CardContent>);
      const content = screen.getByText('Custom Content');
      expect(content).toHaveClass('custom-class');
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(<CardContent ref={ref}>Content</CardContent>);
      expect(ref.current?.constructor.name).toBe('HTMLDivElement');
      expect(ref.current).toHaveTextContent('Content');
    });

    it('has proper display name', () => {
      expect(CardContent.displayName).toBe('CardContent');
    });
  });

  describe('CardFooter', () => {
    it('renders correctly with default props', () => {
      render(<CardFooter>Card Footer</CardFooter>);
      const footer = screen.getByText('Card Footer');
      expect(footer).toBeInTheDocument();
      expect(footer).toHaveClass('flex items-center p-6 pt-0');
    });

    it('renders with custom className', () => {
      render(<CardFooter className="custom-class">Custom Footer</CardFooter>);
      const footer = screen.getByText('Custom Footer');
      expect(footer).toHaveClass('custom-class');
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(<CardFooter ref={ref}>Footer Content</CardFooter>);
      expect(ref.current?.constructor.name).toBe('HTMLDivElement');
      expect(ref.current).toHaveTextContent('Footer Content');
    });

    it('has proper display name', () => {
      expect(CardFooter.displayName).toBe('CardFooter');
    });
  });

  describe('Complete Card Structure', () => {
    it('renders a complete card with all components', () => {
      render(
        <Card data-testid="complete-card">
          <CardHeader>
            <CardTitle>Complete Card Title</CardTitle>
            <CardDescription>Complete Card Description</CardDescription>
          </CardHeader>
          <CardContent>
            <p>This is the main content of card.</p>
          </CardContent>
          <CardFooter>
            <button>Card Action</button>
          </CardFooter>
        </Card>
      );

      const card = screen.getByTestId('complete-card');
      expect(card).toBeInTheDocument();

      expect(screen.getByText('Complete Card Title')).toBeInTheDocument();
      expect(screen.getByText('Complete Card Description')).toBeInTheDocument();
      expect(screen.getByText('This is the main content of card.')).toBeInTheDocument();
      expect(screen.getByText('Card Action')).toBeInTheDocument();

      // Verify structure
      const title = screen.getByText('Complete Card Title');
      expect(title.tagName).toBe('H3');
      expect(title).toHaveClass('text-2xl font-semibold');

      const description = screen.getByText('Complete Card Description');
      expect(description.tagName).toBe('P');
      expect(description).toHaveClass('text-sm text-muted-foreground');
    });

    it('maintains proper semantic structure', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Semantic Title</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Semantic content</p>
          </CardContent>
        </Card>
      );

      const title = screen.getByRole('heading', { name: 'Semantic Title' });
      expect(title).toBeInTheDocument();

      const content = screen.getByText('Semantic content');
      expect(content).toBeInTheDocument();
    });
  });
});
