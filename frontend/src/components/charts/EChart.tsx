'use client';

import * as echarts from 'echarts/core';
import {
  BarChart,
  LineChart,
  MapChart,
  PieChart,
} from 'echarts/charts';
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TitleComponent,
  ToolboxComponent,
  TooltipComponent,
  VisualMapComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { EChartsOption } from 'echarts';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import { useMemo } from 'react';

echarts.use([
  LineChart,
  BarChart,
  PieChart,
  MapChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  DataZoomComponent,
  VisualMapComponent,
  CanvasRenderer,
]);

interface Props {
  option: EChartsOption;
  height?: number | string;
  loading?: boolean;
  className?: string;
}

export function EChart({ option, height = 400, loading, className }: Props) {
  const opts = useMemo(() => ({ renderer: 'canvas' as const }), []);
  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height, width: '100%' }}
      opts={opts}
      showLoading={loading}
      notMerge
      lazyUpdate
      className={className}
    />
  );
}

export { echarts };
