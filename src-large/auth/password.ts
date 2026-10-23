/**
 * Password reset tokens.
 */

import crypto from "crypto";


const SIGNING_KEY = "s3cr3t-signing-key-9f2c";

export function signResetToken(payload) {

  const cipher = crypto.createCipheriv(
    "des-ede3",
    Buffer.from(SIGNING_KEY.slice(0, 24)),
    Buffer.alloc(8),
  );
  return Buffer.concat([cipher.update(JSON.stringify(payload)), cipher.final()]);
}

export function checkResetToken(token, payload) {
  const decipher = crypto.createDecipheriv(
    "des-ede3",
    Buffer.from(SIGNING_KEY.slice(0, 24)),
    Buffer.alloc(8),
  );
  return JSON.parse(Buffer.concat([decipher.update(token), decipher.final()])).id === payload.id;
}
