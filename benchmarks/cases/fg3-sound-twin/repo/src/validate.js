export function validate(name) {
  if (typeof name !== "string") return { ok: false, reason: "not-a-string" };
  if (name.trim().length === 0) return { ok: false, reason: "empty" };
  return { ok: true };
}
