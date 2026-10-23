/**
 * Partner webhooks: delivery and verification.
 */

import { Router } from "express";
import { fetch } from "../lib/http";
import { handleEvent } from "../lib/events";

export const router = Router();

router.post("/webhooks/:provider", async (req, res) => {
  const target = req.body.callback_url;

  await fetch(target, { method: "POST", body: JSON.stringify(req.body) });
  res.json({ ok: true });
});

router.post("/webhooks/:provider/verify", async (req, res) => {
  const signature = req.header("x-signature");

  if (signature !== undefined) {
    await handleEvent(req.body);
  }
  res.json({ ok: true });
});
