import { defineConfig } from 'vitest/config'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { playwright } from '@vitest/browser-playwright'

const dirname =
  typeof __dirname !== 'undefined' ? __dirname : path.dirname(fileURLToPath(import.meta.url))
const designSystemRoot = path.resolve(dirname, '..', '..', 'design-system')
const appUiNodeModules = path.resolve(dirname, 'node_modules')

export default defineConfig(() => {
  const projects = [
    {
      extends: true,
      test: {
        name: 'unit',
        environment: 'jsdom',
        setupFiles: ['vitest.setup.ts'],
        globals: true,
        include: [
          '../../design-system/components/**/*.test.{ts,tsx}',
          'src/**/*.test.{ts,tsx}',
        ],
      },
    },
    {
      extends: true,
      test: {
        name: 'storybook',
        passWithNoTests: true,
        include: ['../../design-system/components/**/*.stories.{ts,tsx}'],
        browser: {
          enabled: true,
          headless: true,
          provider: playwright({}),
          instances: [{ browser: 'chromium' }],
        },
        setupFiles: ['.storybook/vitest.setup.ts'],
      },
    },
  ]

  return {
    define: {
      'process.env': {
        NODE_ENV: 'test',
      },
      process: {
        env: {
          NODE_ENV: 'test',
        },
      },
    },
    optimizeDeps: {
      include: [
        '@storybook/nextjs',
        '@storybook/addon-a11y/preview',
        '@storybook/test',
        '@testing-library/react',
        'axe-core',
        'lucide-react',
        '@radix-ui/react-tooltip',
      ],
    },
    resolve: {
      alias: {
        react: path.join(appUiNodeModules, 'react'),
        'react-dom': path.join(appUiNodeModules, 'react-dom'),
        '@storybook/test': path.join(appUiNodeModules, '@storybook/test'),
        'axe-core': path.join(appUiNodeModules, 'axe-core'),
        'lucide-react': path.join(appUiNodeModules, 'lucide-react'),
        '@radix-ui/react-tooltip': path.join(appUiNodeModules, '@radix-ui/react-tooltip'),
        '@testing-library/react': path.join(appUiNodeModules, '@testing-library/react'),
        '@testing-library/user-event': path.join(
          appUiNodeModules,
          '@testing-library/user-event',
        ),
        '@testing-library/jest-dom': path.join(appUiNodeModules, '@testing-library/jest-dom'),
        clsx: path.join(appUiNodeModules, 'clsx'),
        'tailwind-merge': path.join(appUiNodeModules, 'tailwind-merge'),
      },
    },
    server: {
      fs: {
        allow: [designSystemRoot],
      },
    },
    test: {
      projects,
    },
  }
})
