import { defineConfig } from 'orval'

export default defineConfig({
  web: {
    input: {
      target: '../../packages/openapi/openapi.json',
    },
    output: {
      target: './src/shared/api/generated/web.ts',
      client: 'vue-query',
      httpClient: 'fetch',
      mode: 'single',
      clean: true,
      prettier: true,
      override: {
        fetch: {
          includeHttpResponseReturnType: false,
        },
        mutator: {
          path: './src/shared/api/fetcher.ts',
          name: 'apiFetch',
        },
      },
    },
  },
})
