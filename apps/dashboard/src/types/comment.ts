export type SentimentLabel = "positive" | "neutral" | "negative";

export type SocialComment = {
  platform: string;
  source_type: string;
  source_id: string;
  text: string;
  source_url?: string;
};
