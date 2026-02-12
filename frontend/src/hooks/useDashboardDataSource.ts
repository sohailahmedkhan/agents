"use client";

import { useCallback, useState } from "react";

type DataSource = "raw" | "bigquery";

interface DashboardDataSource {
  dataSource: DataSource;
  setDataSource: (source: DataSource) => void;
}

export function useDashboardDataSource(initial: DataSource = "raw"): DashboardDataSource {
  const [dataSource, setDataSourceState] = useState<DataSource>(initial);

  const setDataSource = useCallback((source: DataSource) => {
    setDataSourceState(source);
  }, []);

  return { dataSource, setDataSource };
}
