# Häuserhofer website (demo)

Static Astro site for the fictional company Häuserhofer Haustechnik GmbH, planned for `demo.haeuserhofer.filandmuz.com`.
All facts come from the company bible; styles come from the Häuserhofer design system v1.0 (`src/styles/tokens.css` is generated from its `tokens.json`).

```bash
npm install
npm run dev        # local dev server
npm run build      # static output in dist/
npm run check:demo # fails if a page misses the demo labels or has forms, tel: links or LocalBusiness schema
```

Photos: every slot is a `Photo` component with a mandatory AI label. Add the generated image under `public/images/` and pass `src`.
