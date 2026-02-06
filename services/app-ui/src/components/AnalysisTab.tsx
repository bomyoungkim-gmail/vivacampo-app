"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CorrelationChart } from "./CorrelationChart";
import { YearOverYearChart } from "./YearOverYearChart";
import api from "@/lib/api";
import { PRODUCTIVITY_HISTORICAL_AVG } from "@/lib/constants";
import { AlertCircle, CloudRain, TrendingDown, Radio } from "lucide-react";

type Insight = {
  type: string;
  message: string;
  severity: string;
};

type CorrelationResponse = {
  data: Array<{
    date: string;
    ndvi: number | null;
    rvi: number | null;
    rain_mm: number | null;
    temp_avg: number | null;
  }>;
  insights: Insight[];
};

type YearOverYearResponse = {
  current_year: number;
  previous_year: number;
  current_series: Array<{ week: number; ndvi: number | null }>;
  previous_series: Array<{ week: number; ndvi: number | null }>;
};

const icons: Record<string, React.ReactNode> = {
  rain_effect: <CloudRain className="h-4 w-4" />,
  vigor_drop: <TrendingDown className="h-4 w-4" />,
  radar_fallback: <Radio className="h-4 w-4" />,
};

export function AnalysisTab({ aoiId }: { aoiId: string }) {
  const [data, setData] = useState<CorrelationResponse | null>(null);
  const [yoy, setYoy] = useState<YearOverYearResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const correlationRequest = api.get(`/v1/app/aois/${aoiId}/correlation/vigor-climate`, { params: { weeks: 12 } });
    const yoyRequest = api.get(`/v1/app/aois/${aoiId}/correlation/year-over-year`);

    Promise.allSettled([correlationRequest, yoyRequest])
      .then((results) => {
        const [correlationResult, yoyResult] = results;
        if (correlationResult.status === "fulfilled") {
          setData(correlationResult.value.data);
        } else {
          console.error(correlationResult.reason);
        }
        if (yoyResult.status === "fulfilled") {
          setYoy(yoyResult.value.data);
        } else {
          console.error(yoyResult.reason);
        }
      })
      .finally(() => setLoading(false));
  }, [aoiId]);

  if (loading) return <Skeleton className="h-[400px] w-full" />;
  if (!data && !yoy) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex h-48 items-center justify-center rounded-lg border border-border bg-muted/40">
            <p className="text-sm text-muted-foreground">Sem dados históricos disponíveis</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const yoyChartData = (() => {
    if (!yoy) return [];
    const merged = new Map<number, { week: number; current: number | null; previous: number | null }>();
    for (const row of yoy.current_series) {
      merged.set(row.week, { week: row.week, current: row.ndvi ?? null, previous: null });
    }
    for (const row of yoy.previous_series) {
      const existing = merged.get(row.week);
      if (existing) {
        existing.previous = row.ndvi ?? null;
      } else {
        merged.set(row.week, { week: row.week, current: null, previous: row.ndvi ?? null });
      }
    }
    return Array.from(merged.values()).sort((a, b) => a.week - b.week);
  })();

  const yoyHasBreakAlert = yoyChartData.some(
    (row) => row.current != null && row.previous != null && row.current < row.previous
  );

  const productivity = (() => {
    if (!data) return null;
    const ndviValues = data.data.map((row) => row.ndvi).filter((v): v is number => v != null);
    if (ndviValues.length === 0) return null;
    const score = ndviValues.reduce((acc, v) => acc + v, 0) / ndviValues.length;
    const historicalAvg = PRODUCTIVITY_HISTORICAL_AVG;
    const deviation = ((score - historicalAvg) / historicalAvg) * 100;
    return { score, historicalAvg, deviation };
  })();

  return (
    <div className="space-y-4">
      {data && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Correlação Vigor x Clima</CardTitle>
          </CardHeader>
          <CardContent>
            <CorrelationChart data={data.data} />
          </CardContent>
        </Card>
      )}
      {productivity && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Potencial Produtivo</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-semibold text-foreground">
              {productivity.score.toFixed(2)}
            </div>
            <p className="text-sm text-muted-foreground">
              Baseado na média da curva NDVI (histórico: {productivity.historicalAvg.toFixed(2)}).
            </p>
            <p className="text-sm text-muted-foreground">
              Sua safra acumulou {Math.abs(productivity.deviation).toFixed(0)}% {productivity.deviation >= 0 ? "acima" : "abaixo"} da média histórica.
            </p>
          </CardContent>
        </Card>
      )}
      {yoy && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Comparação de Safra (Ano a Ano)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <YearOverYearChart
              data={yoyChartData}
              currentYear={yoy.current_year}
              previousYear={yoy.previous_year}
            />
            {yoyHasBreakAlert && (
              <div className="rounded-lg bg-muted/50 p-3 text-sm text-muted-foreground">
                Alerta de quebra: a safra atual cruzou abaixo da anterior em algumas semanas.
              </div>
            )}
          </CardContent>
        </Card>
      )}
      {data && data.insights?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Insights Automáticos</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.insights.map((insight, idx) => (
              <div key={idx} className="flex items-start gap-3 rounded-lg bg-muted/50 p-3">
                {icons[insight.type] || <AlertCircle className="h-4 w-4" />}
                <p className="flex-1 text-sm">{insight.message}</p>
                <Badge variant={insight.severity === "warning" ? "default" : "secondary"}>
                  {insight.severity}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
