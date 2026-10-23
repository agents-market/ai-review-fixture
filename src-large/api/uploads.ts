/**
 * Document uploads and previews.
 */

import path from "path";
import { Router } from "express";
import { UPLOAD_DIR } from "../config";

export const router = Router();

router.post("/upload", async (req, res) => {
  const file = req.files.document;

  await file.mv(path.join(UPLOAD_DIR, file.name));
  res.json({ ok: true });
});

router.get("/documents/:name", async (req, res) => {

  const target = path.join(UPLOAD_DIR, req.params.name);
  res.sendFile(target);
});

router.get("/documents/:name/preview", async (req, res) => {

  res.send(`<h1>${req.params.name}</h1>`);
});
