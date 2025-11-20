// src/components/NewsCard.tsx
import React from "react";
import type { NewsArticle } from "../api/stockApi";

interface NewsCardProps {
  article: NewsArticle & { sentiment: "positive" | "neutral" | "negative"; date: string };
}

const NewsCard: React.FC<NewsCardProps> = ({ article }) => {
  // Format published date
  const publishedDate = new Date(article.date);
  const formattedDate = isNaN(publishedDate.getTime())
    ? "Unknown date"
    : publishedDate.toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });

  // Color code sentiment
  const sentimentColor = {
    positive: "text-green-600",
    neutral: "text-gray-600",
    negative: "text-red-600",
  }[article.sentiment];

  return (
    <div className="mb-2 p-2 border rounded bg-white hover:shadow">
      <h3 className="font-semibold text-sm">{article.title}</h3>
      {article.description && <p className="text-xs text-gray-700">{article.description}</p>}
      <div className="flex justify-between text-xs mt-1">
        <span className={sentimentColor}>{article.sentiment.toUpperCase()}</span>
        <span className="text-gray-500">{formattedDate}</span>
      </div>
    </div>
  );
};

export default NewsCard;
