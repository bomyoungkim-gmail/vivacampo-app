"use client";

import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import api from "@/lib/api";
import type { NitrogenStatus } from "@/lib/types";

type NitrogenAlertProps = {
  aoiId: string;
  status?: NitrogenStatus | null;
  loading?: boolean;
};

export function NitrogenAlert({ aoiId, status: statusProp, loading: loadingProp }: NitrogenAlertProps) {
  const useRemote = statusProp === undefined;
  const [status, setStatus] = useState<NitrogenStatus | null>(useRemote ? null : statusProp ?? null);
  const [loading, setLoading] = useState(useRemote);

  useEffect(() => {
    if (useRemote) return;
    setStatus(statusProp ?? null);
    setLoading(!!loadingProp);
  }, [useRemote, statusProp, loadingProp]);

  useEffect(() => {
    if (!useRemote) return;
    api
      .get(`/v1/app/aois/${aoiId}/nitrogen/status`)
      .then((res) => setStatus(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [aoiId, useRemote]);

  if (loading || !status || status.status !== "DEFICIENT") return null;

  return (
    <Alert variant="destructive" className="mb-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-950">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>Deficiência de Nitrogênio Detectada</AlertTitle>
      <AlertDescription>
        <p className="mt-1 text-sm">{status.recommendation}</p>
        <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
          <span>NDVI: {status.ndvi_mean?.toFixed(2)}</span>
          <span>NDRE: {status.ndre_mean?.toFixed(2)}</span>
          <span>Confiança: {(status.confidence * 100).toFixed(0)}%</span>
        </div>
        {status.zone_map_url && (
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="mt-3">
                Ver Mapa de Zonas
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl">
              <DialogHeader>
                <DialogTitle>Mapa SRRE (Nitrogênio)</DialogTitle>
              </DialogHeader>
              <div className="h-[500px]">
                <iframe
                  src={`/map-embed?aoi=${aoiId}&layer=srre`}
                  className="h-full w-full rounded border-0"
                />
              </div>
            </DialogContent>
          </Dialog>
        )}
      </AlertDescription>
    </Alert>
  );
}
