import express, { type Express } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import router from "./routes";
import { logger } from "./lib/logger";

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return {
          id: req.id,
          method: req.method,
          url: req.url?.split("?")[0],
        };
      },
      res(res) {
        return {
          statusCode: res.statusCode,
        };
      },
    },
  }),
);
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use("/api", router);

// The public Replit /api path is owned by this managed service. Forward
// LogStream API calls to the imported FastAPI service so the public preview
// and the local Vite proxy reach the same authenticated backend.
app.use("/api", async (req, res, next) => {
  const backendUrl = process.env["LOGSTREAM_BACKEND_URL"] || "http://127.0.0.1:8099";
  const target = `${backendUrl}${req.originalUrl}`;
  const method = req.method.toUpperCase();
  const headers: Record<string, string> = {};

  for (const name of ["accept", "authorization", "content-type"]) {
    const value = req.get(name);
    if (value) headers[name] = value;
  }

  const init: RequestInit = { method, headers };
  if (method !== "GET" && method !== "HEAD") {
    init.body = JSON.stringify(req.body ?? {});
    headers["content-type"] ||= "application/json";
  }

  try {
    const upstream = await fetch(target, init);
    const body = Buffer.from(await upstream.arrayBuffer());
    res.status(upstream.status);
    const contentType = upstream.headers.get("content-type");
    if (contentType) res.setHeader("content-type", contentType);
    res.send(body);
  } catch (error) {
    next(error);
  }
});

export default app;
