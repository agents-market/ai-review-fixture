/**
 * The back office.
 */

import { Router } from "express";
import { db } from "../lib/db";

export const router = Router();

router.get("/admin/return", (req, res) => {

  res.redirect(String(req.query.to ?? "/"));
});

router.get("/admin/users/:id", async (req, res) => {

  const user = await db.one("SELECT * FROM users WHERE id = ?", [req.params.id]);
  res.json(user);
});

router.post("/admin/users/:id/role", async (req, res) => {

  await db.query("UPDATE users SET role = ? WHERE id = ?", [req.body.role, req.params.id]);
  res.json({ ok: true });
});
