import { Hono } from "hono";
import type { Env } from "../types/env.js";
import {
  getAvailableTemplates,
  getTemplateInfo,
} from "../engine/template-registry.js";
import { getTemplateMetadata } from "../engine/template-engine.js";
import { ResourceNotFoundError, InternalServerError } from "../errors/exceptions.js";

const app = new Hono<{ Bindings: Env }>();

app.get("/templates", (c) => {
  try {
    const templates = getAvailableTemplates();
    return c.json({ templates });
  } catch (e) {
    throw new InternalServerError(String(e));
  }
});

app.get("/templates/:documentType", (c) => {
  const documentType = c.req.param("documentType");
  try {
    const templates = getAvailableTemplates(documentType);
    if (!templates[documentType]) {
      throw new ResourceNotFoundError(`templates for ${documentType}`);
    }
    return c.json({ templates });
  } catch (e) {
    if (e instanceof ResourceNotFoundError) throw e;
    throw new InternalServerError(String(e));
  }
});

app.get("/template-info/:documentType/:templateName", (c) => {
  const documentType = c.req.param("documentType");
  const templateName = c.req.param("templateName");
  try {
    const info = getTemplateMetadata(documentType, templateName);
    return c.json(info);
  } catch (e) {
    if (e instanceof ResourceNotFoundError) throw e;
    throw new InternalServerError(String(e));
  }
});

export default app;
