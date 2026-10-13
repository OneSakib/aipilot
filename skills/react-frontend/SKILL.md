---
name: react-frontend
description: React and Next.js frontends with TypeScript, hooks and Tailwind
triggers: [react, reactjs, next, nextjs, component, hook, hooks, jsx, tsx, frontend, vite, tailwind, redux, zustand]
---
- Use function components and hooks. Keep one component per file, named after the file.
- Put state as low as possible. Lift it only when siblings need it.
- Extract data fetching and side effects into custom hooks under `hooks/`.
- Type props and API responses with TypeScript interfaces. Avoid `any`.
- Organize by feature: `features/<name>/components`, `hooks`, `api`, `types`.
- Memoize only when a measured render cost justifies it.
- Handle loading, empty and error states in every data-driven view.
