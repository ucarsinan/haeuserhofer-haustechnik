import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://demo.haeuserhofer.filandmuz.com',
  trailingSlash: 'ignore',
  build: { format: 'directory' },
});
