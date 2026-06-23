const { ChartJSNodeCanvas } = require('chartjs-node-canvas');
const fs = require('fs');

const csv = fs.readFileSync('sales-data-clean.csv', 'utf-8');
const lines = csv.split('\n').filter(l => l.trim());
const headers = lines[0].split(',');
const catIdx = headers.indexOf('제품분류');
const amtIdx = headers.indexOf('매출액');

const salesByCategory = {};
for (let i = 1; i < lines.length; i++) {
  const cols = lines[i].split(',');
  if (cols.length <= catIdx) continue;
  const cat = cols[catIdx];
  const amt = parseInt(cols[amtIdx], 10) || 0;
  salesByCategory[cat] = (salesByCategory[cat] || 0) + amt;
}

const sorted = Object.entries(salesByCategory).sort((a, b) => b[1] - a[1]);
const labels = sorted.map(([k]) => k);
const data = sorted.map(([, v]) => parseFloat((v / 100000000).toFixed(2))); // 억 원 단위

const colors = ['#4C72B0', '#DD8452', '#55A868', '#C44E52'];

const width = 1200;
const height = 700;
const canvas = new ChartJSNodeCanvas({ width, height, backgroundColour: 'white' });

const config = {
  type: 'bar',
  data: {
    labels,
    datasets: [{
      label: '총 매출액',
      data,
      backgroundColor: colors,
      borderColor: colors,
      borderWidth: 1,
    }]
  },
  options: {
    plugins: {
      title: {
        display: true,
        text: '2024년 제품분류별 총 매출액',
        font: { size: 20, weight: 'bold' },
        padding: { top: 10, bottom: 24 }
      },
      legend: { display: false },
    },
    scales: {
      x: {
        title: { display: true, text: '제품분류', font: { size: 13 } },
        ticks: { font: { size: 13 } },
        grid: { color: 'rgba(200, 200, 200, 0.4)' }
      },
      y: {
        title: { display: true, text: '총 매출액 (억 원)', font: { size: 13 } },
        ticks: {
          callback: v => v.toFixed(1) + '억',
          font: { size: 11 }
        },
        beginAtZero: true,
        suggestedMax: Math.max(...data) * 1.2,
        grid: { color: 'rgba(200, 200, 200, 0.4)' }
      }
    },
    layout: { padding: { top: 40, right: 30, bottom: 10, left: 10 } },
    animation: false
  },
  plugins: [{
    id: 'dataLabels',
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      chart.data.datasets.forEach((dataset, i) => {
        const meta = chart.getDatasetMeta(i);
        meta.data.forEach((bar, idx) => {
          const value = dataset.data[idx];
          const label = value.toFixed(2) + '억';
          ctx.save();
          ctx.font = 'bold 13px sans-serif';
          ctx.fillStyle = '#333';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'bottom';
          ctx.fillText(label, bar.x, bar.y - 6);
          ctx.restore();
        });
      });
    }
  }]
};

(async () => {
  const buffer = await canvas.renderToBuffer(config);
  fs.writeFileSync('chart-bar.png', buffer);
  console.log('저장 완료: chart-bar.png');
  console.log('카테고리별 매출:');
  sorted.forEach(([k, v]) => console.log(`  ${k}: ${(v / 100000000).toFixed(2)}억 원`));
})();
