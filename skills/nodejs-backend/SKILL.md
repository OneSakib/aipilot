---
name: nodejs-backend
description: Node.js backends with Express or NestJS and TypeScript
triggers: [node, nodejs, express, nestjs, npm, pnpm, prisma, mongoose, middleware, typescript]
---
- Separate routes, controllers, services and data access into their own folders.
- Validate every request body and query with a schema library such as zod.
- Use async/await with one error-handling middleware at the end of the chain.
- Load configuration once from environment variables and export a typed config object.
- Never block the event loop. Offload heavy work to worker threads or a queue.
- Add a `test` and `build` script to package.json and run them after changes.
