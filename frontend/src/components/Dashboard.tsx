// src/components/Dashboard.tsx
import React, { useState, useMemo } from "react";
import { fetchStockData, type StockApiResponse, type NewsArticle } from "../api/stockApi";
import StockCard from "./StockCard";
import NewsCard from "./NewsCard";

// Extend NewsArticle to ensure sentiment and date exist
type NewsWithSentiment = NewsArticle & { sentiment: "positive" | "neutral" | "negative"; date: string };

const Dashboard: React.FC = () => {
  const [symbol, setSymbol] = useState("");
  const [stockData, setStockData] = useState<StockApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filter, setFilter] = useState<"all" | "positive" | "neutral" | "negative">("all");
  const [range, setRange] = useState<number>(1); // default 1 day

  // Load stock + news
  const loadData = async () => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchStockData(symbol);

      const newsWithSentiment: NewsWithSentiment[] = data.data.news.map((a) => ({
        ...a,
        sentiment: (a.sentiment as "positive" | "neutral" | "negative") || "neutral",
        date: a.date || a.fetched_at,
      }));

      console.log("[Dashboard] Fetched news:", newsWithSentiment);

      setStockData({
        ...data,
        data: {
          ...data.data,
          news: newsWithSentiment,
        },
      });
    } catch (err) {
      setError((err as Error).message);
      setStockData(null);
    } finally {
      setLoading(false);
    }
  };

  // Compute filtered articles automatically based on filter + range
  const filteredArticles = useMemo(() => {
    if (!stockData) return [];

    const fromDate = new Date();
    fromDate.setDate(fromDate.getDate() - range);

    const filtered = stockData.data.news
      .filter((a) => filter === "all" || a.sentiment === filter)
      .filter((a) => {
        const articleDate = new Date(a.date);
        return !isNaN(articleDate.getTime()) && articleDate >= fromDate;
      })
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

    console.log("[Dashboard] Filtered articles:", filtered);

    // TEMP: fallback for testing sparklines if empty
    if (filtered.length === 0 && stockData.data.news.length > 0) {
      console.warn("[Dashboard] Filtered out all articles, using full news for testing sparklines");
      return stockData.data.news;
    }

    return filtered;
  }, [stockData, filter, range]);

  return (
    <div className="p-6">
      {/* Input & Fetch */}
      <div className="mb-4 flex flex-wrap gap-2">
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          className="border p-2 rounded flex-1 min-w-[200px]"
          placeholder="Enter stock symbol"
        />
        <button
          onClick={loadData}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Fetch
        </button>
      </div>

      {/* Filters */}
      {stockData && (
        <div className="mb-4 flex flex-wrap gap-2 items-center">
          {(["all", "positive", "neutral", "negative"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded ${
                filter === f
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
          <select
            value={range}
            onChange={(e) => setRange(Number(e.target.value))}
            className="border px-2 py-1 rounded ml-4"
          >
            <option value={1}>1 Day</option>
            <option value={3}>3 Days</option>
            <option value={7}>1 Week</option>
            <option value={14}>2 Weeks</option>
            <option value={30}>1 Month</option>
          </select>
        </div>
      )}

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">Error: {error}</p>}

      {stockData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <StockCard stock={stockData.data.stock_info} news={filteredArticles} />
          <div className="flex flex-col">
            <h2 className="text-xl font-bold mb-2">News</h2>
            <div className="overflow-y-auto h-[400px] p-2 border rounded bg-gray-50">
              {filteredArticles.length === 0 && <p>No news available</p>}
              {filteredArticles.map((article, index) => (
                <NewsCard key={index} article={article} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
