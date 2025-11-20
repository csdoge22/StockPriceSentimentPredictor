// testNewsFiltering.ts
import axios from "axios";

type NewsArticle = {
  title: string;
  description?: string;
  date: string; // ISO string
  sentiment: "positive" | "neutral" | "negative";
};

/**
 * Filters news by sentiment and date range
 */
const filterNewsByDateRange = (
  articles: NewsArticle[],
  sentiment: "all" | "positive" | "neutral" | "negative",
  range: number
) => {
  const fromDate = new Date();
  fromDate.setDate(fromDate.getDate() - range);

  return articles
    .filter((a) => sentiment === "all" || a.sentiment === sentiment)
    .filter((a) => new Date(a.date) >= fromDate)
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
};

const testFiltering = async () => {
  try {
    const symbol = "AAPL"; // test stock
    const res = await axios.get(`http://localhost:8000/stock/${symbol}`);
    const news: NewsArticle[] = res.data.data.news;

    console.log(`Fetched ${news.length} articles from API`);

    const testCases = [
      { sentiment: "all" as const, range: 1 },
      { sentiment: "all" as const, range: 3 },
      { sentiment: "neutral" as const, range: 7 },
      { sentiment: "positive" as const, range: 14 },
    ];

    for (const { sentiment, range } of testCases) {
      const filtered = filterNewsByDateRange(news, sentiment, range);
      console.log(`\n--- Sentiment: ${sentiment}, Range: ${range} days ---`);
      console.log(`Articles after filter: ${filtered.length}`);
      filtered.forEach((a) =>
        console.log(`- ${a.date} [${a.sentiment}] ${a.title}`)
      );
    }
  } catch (err) {
    console.error("Error fetching or filtering news:", err);
  }
};

testFiltering();
