export function generateUserId(): string {
  const stored = localStorage.getItem("digital_me_user_id");
  if (stored) return stored;
  const id = crypto.randomUUID();
  localStorage.setItem("digital_me_user_id", id);
  return id;
}

export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}
