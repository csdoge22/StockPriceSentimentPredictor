// src/components/Dashboard.tsx
import React, { useState, useEffect } from "react";
import { fetchStockData, type StockApiResponse, type NewsArticle } from "../api/stockApi";
import StockCard from "./StockCard";
import NewsCard from "./NewsCard";

interface DashboardProps {
  symbol: string;
  range: "1d" | "3d" | "7d" | "30d";
  fetchTrigger: number;
}

const Dashboard: React.FC<DashboardProps> = ({ symbol, range, fetchTrigger }) => {
  const [activeSymbol, setActiveSymbol] = useState<string>(""); // last fetched ticker
  const [page, setPage] = useState<number>(1);
  const [perPage] = useState<number>(5);
  const [data, setData] = useState<StockApiResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch stock data
  const fetchStock = async () => {
    if (!symbol) return;
    setLoading(true);
    setError(null);

    try {
      const response = await fetchStockData(symbol, page, perPage, "all", range);
      setData(response);
      setActiveSymbol(symbol);
    } catch (err: any) {
      console.error("Error fetching stock data:", err);
      setError(err.message || "Unknown error");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  // Trigger fetch on button click or range change (if same symbol)
  useEffect(() => {
    if (fetchTrigger > 0) {
      fetchStock();
    }
  }, [fetchTrigger]);

  useEffect(() => {
    if (activeSymbol === symbol && activeSymbol !== "") {
      fetchStock();
    }
  }, [range]);

  // Reset pagination when symbol changes
  useEffect(() => {
    setPage(1);
  }, [symbol, range]);

  // Pagination handler
  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    if (activeSymbol === symbol) fetchStock();
  };

  return (
    <div className="p-4">
      {/* Loading / Error */}
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}

      {/* Stock info */}
      {data && (
        <div className="mb-4">
          <StockCard
            data={{
              symbol: data.symbol,
              current_price: data.current_price,
              previous_close: data.previous_close,
              timestamp: data.timestamp,
            }}
          />
        </div>
      )}

      {/* News feed */}
      {data && data.results.length > 0 && (
        <div className="grid gap-4">
          {data.results.map((article: NewsArticle, idx: number) => (
            <NewsCard key={idx} article={article} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && data.total_results > perPage && (
        <div className="flex gap-2 mt-4 justify-center">
          {Array.from({ length: Math.ceil(data.total_results / perPage) }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              onClick={() => handlePageChange(p)}
              className={`px-3 py-1 rounded ${page === p ? "bg-green-500 text-white" : "bg-gray-200"}`}
            >
              {p}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
