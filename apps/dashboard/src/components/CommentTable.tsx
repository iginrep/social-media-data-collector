import type { SocialComment } from "../types/comment";

export function CommentTable({ comments }: { comments: SocialComment[] }) {
  return <table><tbody>{comments.map((c) => <tr key={`${c.platform}-${c.source_id}`}><td>{c.platform}</td><td>{c.text}</td><td>{c.source_url && <a href={c.source_url}>source</a>}</td></tr>)}</tbody></table>;
}
