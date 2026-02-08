import '../../../design-system/tokens.css'

const preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
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
    a11y: {
      test: 'todo'
    }
  },
};

export default preview;
