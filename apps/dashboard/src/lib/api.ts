export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function fetchComments() {
  const res = await fetch(`${API_BASE}/comments`);
  if (!res.ok) throw new Error("failed to fetch comments");
  return res.json();
}
