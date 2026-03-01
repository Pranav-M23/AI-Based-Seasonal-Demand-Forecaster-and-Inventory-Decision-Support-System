import React, { useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { TrendingUp } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

function ForecastChart({ data, category }) {
  const chartData = useMemo(() => {
    if (!data?.series) return null;

    const labels = data.series.map(point => {
      const date = new Date(point.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const values = data.series.map(point => point.value);

    return {
      labels,
      datasets: [
        {
          label: 'Sales Forecast',
          data: values,
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: true,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: '#06b6d4',
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
        }
      ]
    };
  }, [data]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#06b6d4',
        borderWidth: 1,
        displayColors: false,
        callbacks: {
          label: (context) => `Sales: ${context.parsed.y.toLocaleString()}`
        }
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
          drawBorder: false
        },
        ticks: {
          color: '#9ca3af',
          maxRotation: 0,
          autoSkipPadding: 20
        }
      },
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
          drawBorder: false
        },
        ticks: {
          color: '#9ca3af',
          callback: (value) => value.toLocaleString()
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  };

  if (!chartData) {
    return <div className="chart-loading">Loading chart data...</div>;
  }

  return (
    <div className="forecast-chart">
      <div className="chart-header">
        <TrendingUp size={20} />
        <h3>Sales Forecast - {category} Category</h3>
      </div>
      <div className="chart-container">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}

export default ForecastChart;