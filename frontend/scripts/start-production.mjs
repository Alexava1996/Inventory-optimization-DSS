import { cp } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
const root = process.cwd();
await cp(
  path.join(root, ".next/static"),
  path.join(root, ".next/standalone/.next/static"),
  { recursive: true },
);
process.env.HOSTNAME = process.env.LISTEN_HOST || "127.0.0.1";
await import(pathToFileURL(path.join(root, ".next/standalone/server.js")).href);
