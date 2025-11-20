// src/api/stockApi.ts
import axios from "axios";

export interface NewsArticle {
  title: string;
  description: string;
  fetched_at: string; // when it was fetched
  sentiment: "positive" | "negative" | "neutral";
  date: string; // <-- new property for filtering
}

export interface StockInfo {
  current_price: number;
  previous_close: number;
  timestamp: string;
  sentiment_scores?: number[];
}

export interface PaginationInfo {
  page: number;
  per_page: number;
  total_articles: number;
  total_pages: number;
}

export interface StockApiResponse {
  symbol: string;
  data: {
    stock_info: StockInfo;
    news: NewsArticle[];
    pagination: PaginationInfo;
  };
}

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

/**
 * Fetch stock info + paginated/filterable news.
 * @param symbol Stock symbol (e.g., "AAPL")
 * @param page Current page number
 * @param perPage Number of articles per page
 * @param sentiment Filter: "all" | "positive" | "negative" | "neutral"
 */
export const fetchStockData = async (
  symbol: string,
  page = 1,
  perPage = 5,
  sentiment: "all" | "positive" | "negative" | "neutral" = "all"
): Promise<StockApiResponse> => {
  const params = { page, per_page: perPage, sentiment };
  const { data } = await axios.get<StockApiResponse>(`${API_BASE}/stock/${symbol}`, { params });
  return data;
};

/**
 * Send headlines for sentiment prediction
 */
export const predictSentiment = async (headlines: string[]): Promise<string[]> => {
  const { data } = await axios.post(`${API_BASE}/predict`, { headlines });
  return data.sentiments;
};
