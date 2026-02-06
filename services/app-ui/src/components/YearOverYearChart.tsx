"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

type YearOverYearPoint = {
  week: number;
  current: number | null;
  previous: number | null;
};

export function YearOverYearChart({
  data,
  currentYear,
  previousYear,
}: {
  data: YearOverYearPoint[];
  currentYear: number;
  previousYear: number;
}) {
  return (
    <div className="w-full rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="w-full" style={{ height: "260px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
            <XAxis dataKey="week" tick={{ fontSize: 10, fill: "#9ca3af" }} stroke="#e5e7eb" />
            <YAxis domain={[0, 1]} tick={{ fontSize: 10, fill: "#9ca3af" }} stroke="#e5e7eb" />
            <Tooltip
              contentStyle={{
                borderRadius: "8px",
                border: "none",
                boxShadow: "0 10px 15px -3px rgba(0,0,0,0.1)",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
            <Line
              type="monotone"
              dataKey="current"
              name={`Safra ${currentYear}`}
              stroke="#22c55e"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="previous"
              name={`Safra ${previousYear}`}
              stroke="#94a3b8"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
