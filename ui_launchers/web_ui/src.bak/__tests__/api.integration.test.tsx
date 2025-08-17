import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { render, screen, waitFor } from '@testing-library/react';

const server = setupServer(
  rest.get('/api/hello', (_req, res, ctx) => {
    return res(ctx.json({ message: 'hello' }));
  })
);

beforeAll(() => server.listen());
afterAll(() => server.close());
afterEach(() => server.resetHandlers());

test('fetches data from mocked api', async () => {
  const response = await fetch('/api/hello');
  const data = await response.json();
  expect(data).toEqual({ message: 'hello' });
});
