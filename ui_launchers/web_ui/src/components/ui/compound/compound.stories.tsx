import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { Card } from './card';
import { Modal } from './modal';
// import { Form } from './form'; // Temporarily disabled due to type issues
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
type Story = StoryObj<typeof meta>;
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
              <button className="px-4 py-2 bg-gray-200 rounded" aria-label="Button">Cancel</button>
              <button className="px-4 py-2 bg-blue-500 text-white rounded" aria-label="Button">Confirm</button>
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
              <button className="px-4 py-2 bg-blue-500 text-white rounded" aria-label="Button">
              </button>
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
              <button className="w-full px-4 py-2 bg-green-500 text-white rounded" aria-label="Button">
              </button>
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

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

    return (
      <div className="p-8 space-y-8 sm:p-4 md:p-6">
        <h1 className="text-3xl font-bold mb-8">Modal Components</h1>
        <div className="flex gap-4">
          <button 
            onClick={() => setBasicOpen(true)}
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
          </button>
          <button 
            onClick={() => setConfirmOpen(true)}
            className="px-4 py-2 bg-red-500 text-white rounded"
          >
          </button>
          <button 
            onClick={() => setFormOpen(true)}
            className="px-4 py-2 bg-green-500 text-white rounded"
          >
          </button>
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
              <button 
                onClick={() => setBasicOpen(false)}
                className="px-4 py-2 bg-gray-200 rounded"
              >
              </button>
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
              <button 
                onClick={() => setConfirmOpen(false)}
                className="px-4 py-2 bg-gray-200 rounded"
              >
              </button>
              <button 
                onClick={() => setConfirmOpen(false)}
                className="px-4 py-2 bg-red-500 text-white rounded"
              >
              </button>
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
              <button 
                onClick={() => setFormOpen(false)}
                className="px-4 py-2 bg-gray-200 rounded"
              >
              </button>
              <button 
                onClick={() => setFormOpen(false)}
                className="px-4 py-2 bg-blue-500 text-white rounded"
              >
              </button>
            </Modal.Actions>
          </Modal.Content>
        </Modal.Root>
      </div>
    );
  },
};
/**
 * Form Component Examples
 */
export const Forms: Story = {
  render: () => (
    <div className="p-8 space-y-8 max-w-2xl ">
      <h1 className="text-3xl font-bold mb-8">Form Components</h1>
      {/* Basic Form */}
      <Card.Root>
        <Card.Header>
          <Card.Title>Basic Form</Card.Title>
          <Card.Description>
            A simple form with various input types.
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="space-y-4">
            <div>
              <label htmlFor="basic-name" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Full Name</label>
              <input 
                id="basic-name"
                type="text" 
                className="w-full px-3 py-2 border rounded"
                placeholder="Enter your full name" />
            </div>
            <div>
              <label htmlFor="basic-email" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Email Address</label>
              <input 
                id="basic-email"
                type="email" 
                className="w-full px-3 py-2 border rounded"
                placeholder="Enter your email" />
              <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">We'll never share your email with anyone else.</p>
            </div>
            <div>
              <label htmlFor="basic-password" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Password</label>
              <input 
                id="basic-password"
                type="password" 
                className="w-full px-3 py-2 border rounded"
                placeholder="Enter your password" />
            </div>
            <div className="flex justify-end">
              <button className="px-6 py-2 bg-blue-500 text-white rounded" aria-label="Button">
              </button>
            </div>
          </div>
        </Card.Content>
      </Card.Root>
      {/* Form with Validation */}
      <Card.Root>
        <Card.Header>
          <Card.Title>Form with Validation</Card.Title>
          <Card.Description>
            Form showing validation states and error messages.
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="space-y-4">
            <div>
              <label htmlFor="valid-name" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Name (Valid)</label>
              <input 
                id="valid-name"
                type="text" 
                className="w-full px-3 py-2 border border-green-500 rounded"
                value="John Doe"
                readOnly />
              <p className="text-sm text-green-600 mt-1 md:text-base lg:text-lg">Name looks good!</p>
            </div>
            <div>
              <label htmlFor="invalid-email" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Email (Invalid)</label>
              <input 
                id="invalid-email"
                type="email" 
                className="w-full px-3 py-2 border border-red-500 rounded"
                value="invalid-email"
                readOnly />
              <p className="text-sm text-red-600 mt-1 md:text-base lg:text-lg">Please enter a valid email address.</p>
            </div>
            <div>
              <label htmlFor="required-field" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Required Field</label>
              <input 
                id="required-field"
                type="text" 
                className="w-full px-3 py-2 border rounded"
                placeholder="This field is required"
                required />
              <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">This field is required and cannot be empty.</p>
            </div>
            <div className="flex justify-end space-x-2">
              <button className="px-6 py-2 bg-gray-200 rounded" aria-label="Button">
              </button>
              <button className="px-6 py-2 bg-blue-500 text-white rounded" aria-label="Button">
                Validate & Submit
              </button>
            </div>
          </div>
        </Card.Content>
      </Card.Root>
      {/* Complex Form */}
      <Card.Root>
        <Card.Header>
          <Card.Title>Complex Form</Card.Title>
          <Card.Description>
            A more complex form with multiple sections and field types.
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <div className="space-y-6">
            {/* Personal Information Section */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Personal Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="first-name" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">First Name</label>
                  <input 
                    id="first-name"
                    type="text" 
                    className="w-full px-3 py-2 border rounded"
                    placeholder="First name" />
                </div>
                <div>
                  <label htmlFor="last-name" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Last Name</label>
                  <input 
                    id="last-name"
                    type="text" 
                    className="w-full px-3 py-2 border rounded"
                    placeholder="Last name" />
                </div>
              </div>
              <div>
                <label htmlFor="bio" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Bio</label>
                <textarea 
                  id="bio"
                  className="w-full px-3 py-2 border rounded h-24"
                  placeholder="Tell us about yourself..." />
                <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">Brief description about yourself (optional).</p>
              </div>
            </div>
            {/* Contact Information Section */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Contact Information</h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="contact-email" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Email</label>
                  <input 
                    id="contact-email"
                    type="email" 
                    className="w-full px-3 py-2 border rounded"
                    placeholder="your@email.com" />
                </div>
                <div>
                  <label htmlFor="phone" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Phone Number</label>
                  <input 
                    id="phone"
                    type="tel" 
                    className="w-full px-3 py-2 border rounded"
                    placeholder="+1 (555) 123-4567" />
                </div>
              </div>
            </div>
            {/* Preferences Section */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Preferences</h3>
              <div className="space-y-2">
                <div>
                  <label htmlFor="notifications" className="flex items-center">
                    <input 
                      id="notifications"
                      type="checkbox" 
                      className="mr-2" />
                  </label>
                </div>
                <div>
                  <label htmlFor="newsletter" className="flex items-center">
                    <input 
                      id="newsletter"
                      type="checkbox" 
                      className="mr-2" />
                  </label>
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-2">
              <button className="px-6 py-2 bg-gray-200 rounded" aria-label="Button">
              </button>
              <button className="px-6 py-2 bg-blue-500 text-white rounded" aria-label="Button">
              </button>
            </div>
          </div>
        </Card.Content>
      </Card.Root>
    </div>
  ),
};
/**
 * Compound Components Overview
 */
export const Overview: Story = {
  render: () => (
    <div className="p-8 space-y-12 max-w-6xl ">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Compound Components</h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto ">
          consistent styling and behavior patterns.
        </p>
      </div>
      {/* Component Examples Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Card Example */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Card Component</h2>
          <Card.Root>
            <Card.Header>
              <Card.Title>Example Card</Card.Title>
              <Card.Description>
                Flexible card component with composable parts.
              </Card.Description>
            </Card.Header>
            <Card.Content>
              <p className="text-sm text-gray-600 md:text-base lg:text-lg">
                Cards can contain headers, content, and actions in any combination.
              </p>
            </Card.Content>
            <Card.Footer>
              <Card.Actions>
                <button className="px-3 py-1 bg-blue-500 text-white text-sm rounded md:text-base lg:text-lg" aria-label="Button">
                </button>
              </Card.Actions>
            </Card.Footer>
          </Card.Root>
        </div>
        {/* Form Example */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Form Component</h2>
          <Card.Root>
            <Card.Content>
              <div className="space-y-4">
                <div>
                  <label htmlFor="demo-input" className="block text-sm font-medium mb-1 md:text-base lg:text-lg">Demo Input</label>
                  <input 
                    id="demo-input"
                    type="text" 
                    className="w-full px-3 py-2 border rounded text-sm md:text-base lg:text-lg"
                    " />
                  <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">This is a help message.</p>
                </div>
                <div className="flex justify-end">
                  <button className="px-3 py-1 bg-green-500 text-white text-sm rounded md:text-base lg:text-lg" aria-label="Button">
                  </button>
                </div>
              </div>
            </Card.Content>
          </Card.Root>
        </div>
        {/* Modal Trigger Example */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Modal Component</h2>
          <Card.Root>
            <Card.Content>
              <p className="text-sm text-gray-600 mb-4 md:text-base lg:text-lg">
                Modals provide overlay dialogs with flexible content areas.
              </p>
              <button className="px-3 py-1 bg-purple-500 text-white text-sm rounded md:text-base lg:text-lg" aria-label="Button">
              </button>
            </Card.Content>
          </Card.Root>
        </div>
      </div>
      {/* Benefits */}
      <div className="bg-gray-50 rounded-lg p-8 sm:p-4 md:p-6">
        <h2 className="text-2xl font-bold mb-6 text-center">Component Benefits</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-500 rounded-full mx-auto mb-3 flex items-center justify-center ">
              <span className="text-white font-bold">🧩</span>
            </div>
            <h4 className="font-semibold mb-2">Composable</h4>
            <p className="text-sm text-gray-600 md:text-base lg:text-lg">
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-green-500 rounded-full mx-auto mb-3 flex items-center justify-center ">
              <span className="text-white font-bold">🎨</span>
            </div>
            <h4 className="font-semibold mb-2">Consistent</h4>
            <p className="text-sm text-gray-600 md:text-base lg:text-lg">
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-500 rounded-full mx-auto mb-3 flex items-center justify-center ">
              <span className="text-white font-bold">⚡</span>
            </div>
            <h4 className="font-semibold mb-2">Accessible</h4>
            <p className="text-sm text-gray-600 md:text-base lg:text-lg">
              Built-in accessibility features and ARIA support
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-orange-500 rounded-full mx-auto mb-3 flex items-center justify-center ">
              <span className="text-white font-bold">🔧</span>
            </div>
            <h4 className="font-semibold mb-2">TypeScript</h4>
            <p className="text-sm text-gray-600 md:text-base lg:text-lg">
            </p>
          </div>
        </div>
      </div>
    </div>
  ),
};
