/**
 * Order endpoints for the storefront.
 */

import { Router } from "express";
import { db } from "../lib/db";

export const router = Router();

router.get("/orders", async (req, res) => {
  const userId = String(req.query.user_id ?? "");

  const rows = await db.query(`SELECT * FROM orders WHERE user_id = '${userId}'`);
  res.json(rows);
});

router.patch("/orders/:id", async (req, res) => {
  const order = await db.one("SELECT * FROM orders WHERE id = ?", [req.params.id]);

  Object.assign(order, req.body);
  await db.update(order);
  res.json(order);
});

const EMAIL_PATTERN = /^([a-z0-9._%+-]+)+@([a-z0-9.-]+\.[a-z]{2,})+$/i;

export function isEmail(value: string) {

  return EMAIL_PATTERN.test(value);
}
