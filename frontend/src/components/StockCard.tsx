// src/components/StockCard.tsx
import React, { useMemo } from "react";
import SentimentSparkline from "./SentimentSparkline";

interface StockInfo {
  current_price: number;
  previous_close: number;
  timestamp: string;
}

interface NewsArticle {
  sentiment: "positive" | "neutral" | "negative";
}

interface StockCardProps {
  stock: StockInfo;
  news?: NewsArticle[];
}

const StockCard: React.FC<StockCardProps> = ({ stock, news = [] }) => {
  const priceChange = stock.current_price - stock.previous_close;
  const priceChangePercent = ((priceChange / stock.previous_close) * 100).toFixed(2);

  // Compute sentiment scores arrays using -1, 0, 1
  const { negativeScores, neutralScores, positiveScores } = useMemo(() => {
    const neg: number[] = [];
    const neu: number[] = [];
    const pos: number[] = [];

    news.forEach((article) => {
      switch (article.sentiment) {
        case "negative":
          neg.push(-1); // negative goes down
          break;
        case "neutral":
          neu.push(0);  // neutral stays middle
          break;
        case "positive":
          pos.push(1);  // positive goes up
          break;
      }
    });

    console.log("[StockCard] Computed scores:", { negativeScores: neg, neutralScores: neu, positiveScores: pos });
    console.log("[StockCard] News prop:", news);

    return { negativeScores: neg, neutralScores: neu, positiveScores: pos };
  }, [news]);

  return (
    <div className="p-4 border rounded shadow bg-white flex flex-col">
      <h2 className="text-lg font-bold mb-2">Stock Info</h2>
      <p>Current Price: ${stock.current_price.toFixed(2)}</p>
      <p>
        Previous Close: ${stock.previous_close.toFixed(2)} (
        <span className={priceChange >= 0 ? "text-green-600" : "text-red-600"}>
          {priceChange >= 0 ? "+" : ""}
          {priceChange.toFixed(2)} ({priceChangePercent}%)
        </span>
        )
      </p>

      {news.length > 0 && (
        <>
          <h3 className="mt-4 font-semibold">Sentiment Overview</h3>
          <div className="flex gap-2 mt-2">
            <div className="flex-1">
              <p className="text-sm mb-1 text-red-600">Negative</p>
              <SentimentSparkline data={negativeScores} label="negative" />
            </div>
            <div className="flex-1">
              <p className="text-sm mb-1 text-gray-600">Neutral</p>
              <SentimentSparkline data={neutralScores} label="neutral" />
            </div>
            <div className="flex-1">
              <p className="text-sm mb-1 text-green-600">Positive</p>
              <SentimentSparkline data={positiveScores} label="positive" />
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default StockCard;
