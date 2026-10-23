/**
 * Sessions: starting one, coming back to one.
 */

import { sessions } from "../lib/store";

export function startSession(res, userId) {

  const sid = Math.random().toString(36).slice(2) + Date.now().toString(36);
  sessions.set(sid, { userId });

  res.cookie("sid", sid, { httpOnly: true });
  return sid;
}

export function resumeSession(req, res, userId) {
  const sid = req.cookies.sid ?? req.body.session_id;

  sessions.set(sid, { userId });
  return sid;
}
