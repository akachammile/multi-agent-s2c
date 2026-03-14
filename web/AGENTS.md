# Repository Guidelines

## Project Structure & Module Organization
- `src/` contains application code.
- `src/components/` holds Vue SFC UI modules (for example `AgentComponent.vue`, `SidebarComponent.vue`).
- `src/api/` contains API client logic (`agent.ts`, shared exports in `index.ts`).
- `src/assets/` stores static assets and global styles (`css/main.css`).
- `public/` serves static files copied as-is at build time.
- Root config files include `vite.config.ts`, `tsconfig.json`, and `eslint.config.js`.

## Build, Test, and Development Commands
- `npm install`: install dependencies.
- `npm run dev`: start Vite dev server with hot reload.
- `npm run build`: run TypeScript checks (`vue-tsc -b`) and create a production build.
- `npm run preview`: serve the built app locally for verification.
- `npx eslint . --ext .ts,.vue`: run lint checks (no dedicated npm script yet).

## Coding Style & Naming Conventions
- Use TypeScript and Vue 3 `<script setup>` SFCs.
- Indentation: 2 spaces; keep imports grouped and sorted logically (framework, third-party, local).
- Component files use PascalCase (for example `MessageInputArea.vue`).
- API/util modules use lower-case file names where established (for example `agent.ts`).
- Follow ESLint flat config (`eslint.config.js`); avoid adding Prettier-only formatting rules.

## Testing Guidelines
- No automated test framework is currently configured in `package.json`.
- For now, validate changes with:
  1. `npm run build` (type safety + production bundle)
  2. `npm run preview` (manual behavior check)
- If adding tests, prefer Vitest + Vue Test Utils and colocate as `*.spec.ts` beside source files.

## Commit & Pull Request Guidelines
- Current history is minimal (`Initial commit`), so adopt Conventional Commits going forward (for example `feat: add streaming agent panel`).
- Keep commits focused and atomic; avoid mixing refactor and feature work.
- PRs should include:
  - clear summary of behavior changes,
  - linked issue/task ID when available,
  - screenshots or short recordings for UI changes,
  - local verification notes (`npm run build`, lint status).

## Security & Configuration Tips
- Keep environment-specific values in `.env.*` files (never commit secrets).
- Validate outbound API URLs and request payloads in `src/api/` before release.
