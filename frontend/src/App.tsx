// src/App.tsx
import React, { useState } from "react";
import Header from "./components/Header";
import Dashboard from "./components/Dashboard";

const App: React.FC = () => {
  const [symbol, setSymbol] = useState<string>(""); // empty on load
  const [range, setRange] = useState<"1d" | "3d" | "7d" | "30d">("1d");
  const [fetchTrigger, setFetchTrigger] = useState<number>(0); // trigger fetch when button clicked

  const handleFetch = () => {
    if (!symbol) return;
    setFetchTrigger(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />

      <main className="py-6 px-4 text-center">
        {/* Symbol input + range selector + fetch button */}
        <div className="mb-4 flex justify-center gap-2">
          <input
            type="text"
            placeholder="Enter stock symbol (e.g., AAPL)"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="border border-gray-300 rounded px-2 py-1"
          />
          <select
            value={range}
            onChange={(e) =>
              setRange(e.target.value as "1d" | "3d" | "7d" | "30d")
            }
            className="border border-gray-300 rounded px-2 py-1"
          >
            <option value="1d">1 Day</option>
            <option value="3d">3 Days</option>
            <option value="7d">1 Week</option>
            <option value="30d">1 Month</option>
          </select>
          <button
            onClick={handleFetch}
            className="bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700"
          >
            Fetch
          </button>
        </div>

        {/* Dashboard */}
        <Dashboard
          symbol={symbol}
          range={range}
          fetchTrigger={fetchTrigger}
        />
      </main>
    </div>
  );
};

export default App;
