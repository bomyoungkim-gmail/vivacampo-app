import type { Preview } from '@storybook/react';
import '../../tokens.css';

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#FFFFFF' },
        { name: 'dark', value: '#0F172A' },
        { name: 'map', value: '#E5E7EB' },
      ],
    },
  },
};

export default preview;
