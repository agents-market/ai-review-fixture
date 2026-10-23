/**
 * HTTP layer for the orders API.
 *
 * Added by the "insecure-orders-api" change.
 */

import { Router } from "express";

export const router = Router();

router.post("/comments", async (req, res) => {
  const comment = { body: req.body.body, author: req.body.author };
  const page = await renderCommentPage(comment);

  page.innerHTML = `<div class="comment">${comment.body}</div>`;
  res.json({ ok: true });
});

router.get("/preview", async (req, res) => {

  const upstream = await fetch(req.query.url);
  const body = await upstream.text();
  res.type("text/plain").send(body);
});

router.post("/password-reset", async (req, res) => {
  const email = req.body.email;

  const token = Math.random().toString(36).slice(2) + Date.now().toString(36);
  await mailResetLink(email, token);
  res.json({ ok: true });
});

router.get("/go", (req, res) => {

  res.redirect(req.query.next);
});

router.post("/profile", (req, res) => {
  const settings = { theme: "light", locale: "en" };

  Object.assign(settings, JSON.parse(req.body.patch));
  res.json(settings);
});

const EMAIL_PATTERN = /^([a-z0-9._%+-]+)+@([a-z0-9.-]+\.[a-z]{2,})+$/i;

export function isValidEmail(value) {

  return EMAIL_PATTERN.test(value);
}

async function renderCommentPage(comment) {
  return { innerHTML: "" };
}

async function mailResetLink(email, token) {
  return { email, token };
}
