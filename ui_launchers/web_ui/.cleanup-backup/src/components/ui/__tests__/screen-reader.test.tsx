/**
 * Tests for Screen Reader components
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import {
  ScreenReaderOnly,
  VisuallyHidden,
  ScreenReaderAnnouncer,
  DescriptiveText,
  HeadingStructure,
  LandmarkRegion,
  StatusMessage,
  LoadingAnnouncement,
  InteractionDescription,
  useScreenReaderAnnouncements,
} from '../screen-reader';

// Mock component to test the hook
const TestAnnouncementComponent = () => {
  const { 
    announce, 
    announceNavigation, 
    announceAction, 
    announceError, 
    announceSuccess, 
    announceLoading 
  } = useScreenReaderAnnouncements();

  return (
    <div>
      <button onClick={() => announce('Test message', 'polite')}>
        Announce
      </button>
      <button onClick={() => announceNavigation('Home page')}>
        Announce Navigation
      </button>
      <button onClick={() => announceAction('Save')}>
        Announce Action
      </button>
      <button onClick={() => announceError('Something went wrong')}>
        Announce Error
      </button>
      <button onClick={() => announceSuccess('Operation completed')}>
        Announce Success
      </button>
      <button onClick={() => announceLoading('Loading data')}>
        Announce Loading
      </button>
    </div>
  );
};

describe('ScreenReaderOnly', () => {
  it('should render content with sr-only class', () => {
    render(<ScreenReaderOnly>Hidden content</ScreenReaderOnly>);
    
    const element = screen.getByText('Hidden content');
    expect(element).toHaveClass('sr-only');
    expect(element.tagName).toBe('SPAN');
  });

  it('should render as div when asDiv is true', () => {
    render(<ScreenReaderOnly asDiv>Hidden content</ScreenReaderOnly>);
    
    const element = screen.getByText('Hidden content');
    expect(element.tagName).toBe('DIV');
  });

  it('should accept custom className', () => {
    render(<ScreenReaderOnly className="custom-class">Hidden content</ScreenReaderOnly>);
    
    const element = screen.getByText('Hidden content');
    expect(element).toHaveClass('sr-only', 'custom-class');
  });
});

describe('VisuallyHidden', () => {
  it('should be an alias for ScreenReaderOnly', () => {
    render(<VisuallyHidden>Hidden content</VisuallyHidden>);
    
    const element = screen.getByText('Hidden content');
    expect(element).toHaveClass('sr-only');
  });
});

describe('ScreenReaderAnnouncer', () => {
  it('should provide announce function to children', () => {
    const TestChild = ({ announce }: { announce: (message: string) => void }) => (
      <button onClick={() => announce('Test announcement')}>
        Announce
      </button>
    );

    render(
      <ScreenReaderAnnouncer>
        {(announce) => <TestChild announce={announce} />}
      </ScreenReaderAnnouncer>
    );

    const button = screen.getByText('Announce');
    expect(button).toBeInTheDocument();
  });

  it('should render live regions', () => {
    render(
      <ScreenReaderAnnouncer>
        {() => <div>Test content</div>}
      </ScreenReaderAnnouncer>
    );

    // Should have polite and assertive live regions
    const politeRegion = document.getElementById('polite-announcer');
    const assertiveRegion = document.getElementById('assertive-announcer');
    
    expect(politeRegion).toBeInTheDocument();
    expect(assertiveRegion).toBeInTheDocument();
    expect(politeRegion).toHaveAttribute('aria-live', 'polite');
    expect(assertiveRegion).toHaveAttribute('aria-live', 'assertive');
  });
});

describe('DescriptiveText', () => {
  it('should render description with generated ID', () => {
    render(<DescriptiveText description="This is a description" />);
    
    const element = screen.getByText('This is a description');
    expect(element).toHaveClass('sr-only');
    expect(element).toHaveAttribute('id');
  });

  it('should use custom description ID', () => {
    render(<DescriptiveText description="Description" descriptionId="custom-desc" />);
    
    const element = screen.getByText('Description');
    expect(element).toHaveAttribute('id', 'custom-desc');
  });

  it('should be visible when visuallyHidden is false', () => {
    render(<DescriptiveText description="Visible description" visuallyHidden={false} />);
    
    const element = screen.getByText('Visible description');
    expect(element).not.toHaveClass('sr-only');
  });
});

describe('HeadingStructure', () => {
  it('should render correct heading level', () => {
    render(<HeadingStructure level={2}>Test Heading</HeadingStructure>);
    
    const heading = screen.getByRole('heading', { level: 2 });
    expect(heading).toHaveTextContent('Test Heading');
    expect(heading.tagName).toBe('H2');
  });

  it('should apply visual level styling', () => {
    render(<HeadingStructure level={3} visualLevel={1}>Large Heading</HeadingStructure>);
    
    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toHaveClass('text-4xl');
  });

  it('should accept custom className', () => {
    render(<HeadingStructure level={1} className="custom-heading">Heading</HeadingStructure>);
    
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toHaveClass('heading-structure', 'font-semibold', 'custom-heading');
  });
});

describe('LandmarkRegion', () => {
  it('should render correct landmark elements', () => {
    const { rerender } = render(
      <LandmarkRegion landmark="main">Main content</LandmarkRegion>
    );
    
    expect(screen.getByRole('main')).toBeInTheDocument();

    rerender(<LandmarkRegion landmark="navigation">Navigation</LandmarkRegion>);
    expect(screen.getByRole('navigation')).toBeInTheDocument();

    rerender(<LandmarkRegion landmark="banner">Banner</LandmarkRegion>);
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });

  it('should use region role for generic landmark', () => {
    render(<LandmarkRegion landmark="region" label="Custom region">Content</LandmarkRegion>);
    
    const region = screen.getByRole('region');
    expect(region).toHaveAttribute('aria-label', 'Custom region');
  });

  it('should support aria-labelledby', () => {
    render(
      <div>
        <h2 id="section-title">Section Title</h2>
        <LandmarkRegion landmark="region" labelledBy="section-title">
          Content
        </LandmarkRegion>
      </div>
    );
    
    const region = screen.getByRole('region');
    expect(region).toHaveAttribute('aria-labelledby', 'section-title');
  });
});

describe('StatusMessage', () => {
  it('should render with correct role and attributes', () => {
    render(<StatusMessage message="Status update" type="info" />);
    
    const status = screen.getByText('Status update');
    expect(status).toHaveAttribute('role', 'status');
    expect(status).toHaveAttribute('aria-live', 'polite');
    expect(status).toHaveClass('sr-only');
  });

  it('should use alert role for error messages', () => {
    render(<StatusMessage message="Error occurred" type="error" />);
    
    const alert = screen.getByText('Error: Error occurred');
    expect(alert).toHaveAttribute('role', 'alert');
    expect(alert).toHaveAttribute('aria-live', 'assertive');
  });

  it('should prefix message with type', () => {
    render(<StatusMessage message="Operation successful" type="success" />);
    
    expect(screen.getByText('Success: Operation successful')).toBeInTheDocument();
  });

  it('should not announce when announce is false', () => {
    render(<StatusMessage message="Silent message" announce={false} />);
    
    const element = screen.getByText('Silent message');
    expect(element).not.toHaveAttribute('aria-live');
  });
});

describe('LoadingAnnouncement', () => {
  it('should announce loading state', () => {
    render(<LoadingAnnouncement loading={true} />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should use custom loading message', () => {
    render(<LoadingAnnouncement loading={true} loadingMessage="Saving data..." />);
    
    expect(screen.getByText('Saving data...')).toBeInTheDocument();
  });

  it('should announce completion when loading changes to false', () => {
    const { rerender } = render(<LoadingAnnouncement loading={true} />);
    
    // The component needs a re-render cycle to detect the change
    rerender(<LoadingAnnouncement loading={false} />);
    
    // Check if the completion message appears (it should be prefixed with "Success:")
    expect(screen.getByText('Success: Loading complete')).toBeInTheDocument();
  });

  it('should announce error when error is true', () => {
    render(<LoadingAnnouncement loading={false} error={true} />);
    
    expect(screen.getByText('Error: Loading failed')).toBeInTheDocument();
  });
});

describe('InteractionDescription', () => {
  it('should render description with ID', () => {
    render(
      <InteractionDescription 
        description="Use arrow keys to navigate"
        id="nav-desc"
      />
    );
    
    const element = screen.getByText('Use arrow keys to navigate');
    expect(element.closest('div')).toHaveAttribute('id', 'nav-desc');
    expect(element.closest('div')).toHaveClass('sr-only');
  });

  it('should render keyboard shortcuts', () => {
    render(
      <InteractionDescription 
        description="Navigation help"
        shortcuts={['Arrow keys: Navigate', 'Enter: Select']}
      />
    );
    
    expect(screen.getByText('Keyboard shortcuts:')).toBeInTheDocument();
    expect(screen.getByText('Arrow keys: Navigate')).toBeInTheDocument();
    expect(screen.getByText('Enter: Select')).toBeInTheDocument();
  });

  it('should render instructions', () => {
    render(
      <InteractionDescription 
        description="Help text"
        instructions={['Step 1: Click button', 'Step 2: Fill form']}
      />
    );
    
    expect(screen.getByText('Instructions:')).toBeInTheDocument();
    expect(screen.getByText('Step 1: Click button')).toBeInTheDocument();
    expect(screen.getByText('Step 2: Fill form')).toBeInTheDocument();
  });
});

describe('useScreenReaderAnnouncements', () => {
  it('should provide announcement functions', () => {
    render(<TestAnnouncementComponent />);
    
    expect(screen.getByText('Announce')).toBeInTheDocument();
    expect(screen.getByText('Announce Navigation')).toBeInTheDocument();
    expect(screen.getByText('Announce Action')).toBeInTheDocument();
    expect(screen.getByText('Announce Error')).toBeInTheDocument();
    expect(screen.getByText('Announce Success')).toBeInTheDocument();
    expect(screen.getByText('Announce Loading')).toBeInTheDocument();
  });

  it('should call announcement functions without errors', () => {
    render(<TestAnnouncementComponent />);
    
    // These should not throw errors
    fireEvent.click(screen.getByText('Announce'));
    fireEvent.click(screen.getByText('Announce Navigation'));
    fireEvent.click(screen.getByText('Announce Action'));
    fireEvent.click(screen.getByText('Announce Error'));
    fireEvent.click(screen.getByText('Announce Success'));
    fireEvent.click(screen.getByText('Announce Loading'));
  });
});