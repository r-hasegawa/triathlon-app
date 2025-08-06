import { ChartDataPoint } from '@/types/sensor';

export const formatChartData = (data: ChartDataPoint[]) => {
  return {
    labels: data.map(point => new Date(point.timestamp).toLocaleTimeString('ja-JP', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })),
    datasets: [
      {
        label: '体表温度',
        data: data.map(point => point.temperature),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgb(59, 130, 246)',
        pointBorderColor: 'white',
        pointBorderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
      }
    ]
  };
};

export const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
    },
    title: {
      display: true,
      text: 'センサデータ推移',
      font: {
        size: 16,
        weight: 'bold',
      }
    },
    tooltip: {
      callbacks: {
        label: (context: any) => `体表温度: ${context.parsed.y.toFixed(2)}°C`,
        title: (context: any) => {
          const timestamp = context[0]?.label;
          return `時刻: ${timestamp}`;
        }
      }
    }
  },
  scales: {
    x: {
      title: {
        display: true,
        text: '時刻'
      },
      grid: {
        display: true,
        color: 'rgba(0, 0, 0, 0.05)',
      }
    },
    y: {
      title: {
        display: true,
        text: '温度 (°C)'
      },
      grid: {
        display: true,
        color: 'rgba(0, 0, 0, 0.05)',
      },
      suggestedMin: 35.0,
      suggestedMax: 38.0,
    }
  },
  interaction: {
    intersect: false,
    mode: 'index' as const,
  }
};