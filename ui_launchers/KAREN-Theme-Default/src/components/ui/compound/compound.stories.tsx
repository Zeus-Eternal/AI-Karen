import React, { useState, useEffect } from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { Card } from './card';
import { Modal } from './modal';
import { Button } from './button'; // Make sure Button is correctly imported
import { useState } from 'react';
import { useEffect } from 'react';

/**
 * Compound Components for visual regression testing
 */
const meta: Meta = {
  title: 'Components/Compound Components',
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Modern compound components with consistent API patterns.',
      },
    },
  },
};
export default meta;
export type Story = StoryObj<typeof meta>;

/**
 * Card Component Examples
 */
export const Cards: Story = {
  render: () => (
    <div className="p-8 space-y-8 max-w-4xl ">
      <h1 className="text-3xl font-bold mb-8">Card Components</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Basic Card */}
        <Card.Root>
          <Card.Header>
            <Card.Title>Basic Card</Card.Title>
            <Card.Description>
              A simple card with title and description.
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <p>This is the main content area of the card.</p>
          </Card.Content>
        </Card.Root>
        {/* Card with Actions */}
        <Card.Root>
          <Card.Header>
            <Card.Title>Card with Actions</Card.Title>
            <Card.Description>
              Card featuring action buttons in the footer.
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <p>Content with actionable items below.</p>
          </Card.Content>
          <Card.Footer>
            <Card.Actions>
              <Button className="px-4 py-2 bg-gray-200 rounded" aria-label="Button">Cancel</Button>
              <Button className="px-4 py-2 bg-blue-500 text-white rounded" aria-label="Button">Confirm</Button>
            </Card.Actions>
          </Card.Footer>
        </Card.Root>
        {/* Interactive Card */}
        <Card.Root interactive>
          <Card.Header>
            <Card.Title>Interactive Card</Card.Title>
            <Card.Description>
              This card has hover effects and is clickable.
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <p>Hover over this card to see the interactive effects.</p>
          </Card.Content>
        </Card.Root>
        {/* Elevated Card */}
        <Card.Root variant="elevated">
          <Card.Header>
            <Card.Title>Elevated Card</Card.Title>
            <Card.Description>
              Card with elevated shadow styling.
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <p>This card has a more prominent shadow.</p>
          </Card.Content>
        </Card.Root>
        {/* Card with Image */}
        <Card.Root>
          <div className="h-32 bg-gradient-to-r from-blue-400 to-purple-500"></div>
          <Card.Header>
            <Card.Title>Card with Image</Card.Title>
            <Card.Description>
              Card featuring a header image.
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <p>Content below the image header.</p>
          </Card.Content>
          <Card.Footer>
            <Card.Actions justify="end">
              <Button className="px-4 py-2 bg-blue-500 text-white rounded" aria-label="Button">Action</Button>
            </Card.Actions>
          </Card.Footer>
        </Card.Root>
        {/* Complex Card */}
        <Card.Root>
          <Card.Header>
            <Card.Title>Complex Card</Card.Title>
            <Card.Description>
              A more complex card with multiple content sections.
            </Card.Description>
          </Card.Header>
          <Card.Content>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold">Features</h4>
                <ul className="text-sm text-gray-600 list-disc list-inside md:text-base lg:text-lg">
                  <li>Feature one</li>
                  <li>Feature two</li>
                  <li>Feature three</li>
                </ul>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">$29</span>
                <span className="text-sm text-gray-500 md:text-base lg:text-lg">per month</span>
              </div>
            </div>
          </Card.Content>
          <Card.Footer>
            <Card.Actions>
              <Button className="w-full px-4 py-2 bg-green-500 text-white rounded" aria-label="Button">Subscribe</Button>
            </Card.Actions>
          </Card.Footer>
        </Card.Root>
      </div>
    </div>
  ),
};

/**
 * Modal Component Examples
 */
export const Modals: Story = {
  render: () => {
    const [basicOpen, setBasicOpen] = useState(false);
    const [confirmOpen, setConfirmOpen] = useState(false);
    const [formOpen, setFormOpen] = useState(false);

    useEffect(() => {
      const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === 'Escape') {
          // Handle escape key
          setBasicOpen(false);
          setConfirmOpen(false);
          setFormOpen(false);
        }
      };
      
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }, []);

    return (
      <div className="p-8 space-y-8 sm:p-4 md:p-6">
        <h1 className="text-3xl font-bold mb-8">Modal Components</h1>
        <div className="flex gap-4">
          <Button 
            onClick={() => setBasicOpen(true)}
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            Open Basic Modal
          </Button>
          <Button 
            onClick={() => setConfirmOpen(true)}
            className="px-4 py-2 bg-red-500 text-white rounded"
          >
            Open Confirm Modal
          </Button>
          <Button 
            onClick={() => setFormOpen(true)}
            className="px-4 py-2 bg-green-500 text-white rounded"
          >
            Open Form Modal
          </Button>
        </div>

        {/* Basic Modal */}
        <Modal.Root open={basicOpen} onOpenChange={setBasicOpen}>
          <Modal.Content>
            <Modal.Header>
              <Modal.Title>Basic Modal</Modal.Title>
              <Modal.Description>
                This is a basic modal with title and description.
              </Modal.Description>
            </Modal.Header>
            <Modal.Body>
              <p>
                This is the main content of the modal. You can put any content here
                including text, forms, images, or other components.
              </p>
            </Modal.Body>
            <Modal.Actions>
              <Button 
                onClick={() => setBasicOpen(false)}
                className="px-4 py-2 bg-gray-200 rounded"
              >
                Close
              </Button>
            </Modal.Actions>
          </Modal.Content>
        </Modal.Root>

        {/* Confirmation Modal */}
        <Modal.Root open={confirmOpen} onOpenChange={setConfirmOpen}>
          <Modal.Content>
            <Modal.Header>
              <Modal.Title>Confirm Action</Modal.Title>
              <Modal.Description>
                Are you sure you want to perform this action?
              </Modal.Description>
            </Modal.Header>
            <Modal.Body>
              <p className="text-gray-600">
                This action cannot be undone. Please confirm that you want to proceed.
              </p>
            </Modal.Body>
            <Modal.Actions>
              <Button 
                onClick={() => setConfirmOpen(false)}
                className="px-4 py-2 bg-gray-200 rounded"
              >
                Cancel
              </Button>
              <Button 
                onClick={() => setConfirmOpen(false)}
                className="px-4 py-2 bg-red-500 text-white rounded"
              >
                Confirm
              </Button>
            </Modal.Actions>
          </Modal.Content>
        </Modal.Root>

        {/* Form Modal */}
        <Modal.Root open={formOpen} onOpenChange={setFormOpen}>
          <Modal.Content>
            <Modal.Header>
              <Modal.Title>Contact Form</Modal.Title>
              <Modal.Description>
                Fill out the form below to get in touch.
              </Modal.Description>
            </Modal.Header>
            <Modal.Body>
              <div className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Name</label>
                  <input 
                    id="name"
                    type="text" 
                    className="w-full px-3 py-2 border rounded"
                    placeholder="Your name" />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Email</label>
                  <input 
                    id="email"
                    type="email" 
                    className="w-full px-3 py-2 border rounded"
                    placeholder="your@email.com" />
                </div>
                <div>
                  <label htmlFor="message" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Message</label>
                  <textarea 
                    id="message"
                    className="w-full px-3 py-2 border rounded h-24"
                    placeholder="Your message..." />
                </div>
              </div>
            </Modal.Body>
            <Modal.Actions>
              <Button 
                onClick={() => setFormOpen(false)}
                className="px-4 py-2 bg-gray-200 rounded"
              >
                Cancel
              </Button>
              <Button 
                onClick={() => setFormOpen(false)}
                className="px-4 py-2 bg-blue-500 text-white rounded"
              >
                Submit
              </Button>
            </Modal.Actions>
          </Modal.Content>
        </Modal.Root>
      </div>
    );
  },
};
