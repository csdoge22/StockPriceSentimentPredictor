// src/components/NewsCard.tsx
import React from "react";
import type { NewsArticle } from "../api/stockApi";

interface NewsCardProps {
  article: NewsArticle;
}

const sentimentColor = (sentiment: string) => {
  switch (sentiment) {
    case "positive":
      return "text-green-600";
    case "negative":
      return "text-red-600";
    case "neutral":
    default:
      return "text-gray-600";
  }
};

const NewsCard: React.FC<NewsCardProps> = ({ article }) => {
  return (
    <div className="bg-white shadow rounded p-4 border-l-4" style={{ borderColor: "" }}>
      <h3 className="font-semibold text-lg">{article.title}</h3>
      <p className="text-gray-700">{article.description}</p>
      <div className="mt-2 flex justify-between text-sm">
        <span className={sentimentColor(article.sentiment)}>
          Sentiment: {article.sentiment.charAt(0).toUpperCase() + article.sentiment.slice(1)}
        </span>
        <span className="text-gray-500">{new Date(article.date).toLocaleDateString()}</span>
      </div>
    </div>
  );
};

export default NewsCard;
