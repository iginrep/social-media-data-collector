import { CommentTable } from "../components/CommentTable";
import { KeywordManager } from "../components/KeywordManager";
import { ScheduleManager } from "../components/ScheduleManager";
import { SentimentChart } from "../components/SentimentChart";

export default function Home() {
  return <main><h1>BNI BIONS Sentiment Dashboard</h1><KeywordManager /><ScheduleManager /><SentimentChart /><CommentTable comments={[]} /></main>;
}
