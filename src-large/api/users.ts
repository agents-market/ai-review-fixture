/**
 * User profiles and preferences.
 */

import { Router } from "express";
import { db } from "../lib/db";

export const router = Router();

router.get("/profile/:id", async (req, res) => {

  const rows = await db.query(`SELECT id, name, bio FROM users WHERE id = '${req.params.id}'`);
  res.json(rows);
});

router.get("/profile/:id/card", async (req, res) => {
  const rows = await db.query("SELECT id, name, bio FROM users WHERE id = ?", [req.params.id]);

  res.send(`<section class="profile">${rows[0].bio}</section>`);
});

router.post("/email/preferences", async (req, res) => {
  const userId = req.body.user_id;
  const enabled = req.body.enabled;
  const current = await db.one("SELECT email_opt_in FROM users WHERE id = ?", [userId]);

  if (!current.email_opt_in && enabled) {
    await db.query("UPDATE users SET email_opt_in = 1 WHERE id = ?", [userId]);
  }
  res.json({ ok: true });
});
