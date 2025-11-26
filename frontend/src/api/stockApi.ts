// src/api/stockApi.ts
export interface NewsArticle {
  title: string;
  description: string;
  sentiment: string;
  date: string;
}

export interface StockApiResponse {
  results: NewsArticle[];
  symbol: string;
  page: number;
  per_page: number;
  total_results: number;
  current_price: number;
  previous_close: number;
  timestamp: string;
}

const API_BASE = "http://localhost:8000"; // adjust if using a different backend URL

export const fetchStockData = async (
  symbol: string,
  page: number = 1,
  per_page: number = 5,
  sentiment: "all" | "positive" | "negative" | "neutral" = "all",
  range: "1d" | "3d" | "7d" | "30d" = "1d"
): Promise<StockApiResponse> => {
  const url = `${API_BASE}/stock/${symbol}?page=${page}&per_page=${per_page}&sentiment=${sentiment}&range=${range}`;

  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`Error fetching stock data: ${res.statusText}`);
  }

  const data = await res.json();

  // Ensure all fields exist to satisfy TypeScript
  const stockData: StockApiResponse = {
    symbol: data.symbol ?? symbol,
    page: data.page ?? page,
    per_page: data.per_page ?? per_page,
    total_results: data.total_results ?? (data.results?.length ?? 0),
    current_price: data.current_price ?? 0,
    previous_close: data.previous_close ?? 0,
    timestamp: data.timestamp ?? new Date().toISOString(),
    results: Array.isArray(data.results)
      ? data.results.map((a: any) => ({
          title: a.title ?? "No title",
          description: a.description ?? "No description",
          sentiment: a.sentiment ?? "neutral",
          date: a.date ?? new Date().toISOString(),
        }))
      : [],
  };

  return stockData;
};
