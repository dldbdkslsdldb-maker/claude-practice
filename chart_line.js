const { ChartJSNodeCanvas } = require('chartjs-node-canvas');
const fs = require('fs');

const csv = fs.readFileSync('sales-data-clean.csv', 'utf-8');
const lines = csv.split('\n').filter(l => l.trim());
const headers = lines[0].split(',');
const dateIdx = headers.indexOf('주문일');
const amtIdx = headers.indexOf('매출액');

const salesByMonth = {};
for (let i = 1; i < lines.length; i++) {
  const cols = lines[i].split(',');
  if (cols.length <= dateIdx) continue;
  const month = cols[dateIdx].trim();
  const amt = parseInt(cols[amtIdx], 10) || 0;
  salesByMonth[month] = (salesByMonth[month] || 0) + amt;
}

const sorted = Object.entries(salesByMonth).sort(([a], [b]) => a.localeCompare(b));
const labels = sorted.map(([k]) => parseInt(k.replace('2024-', ''), 10) + '월');
const data = sorted.map(([, v]) => parseFloat((v / 100000000).toFixed(2)));

const maxVal = Math.max(...data);
const minVal = Math.min(...data);
const maxIdx = data.indexOf(maxVal);
const minIdx = data.indexOf(minVal);

// 포인트마다 색상·크기 지정 (최고: 빨강, 최저: 주황, 일반: 파랑)
const pointColors = data.map((_, i) => {
  if (i === maxIdx) return '#E74C3C';
  if (i === minIdx) return '#E67E22';
  return '#2563EB';
});
const pointRadii = data.map((_, i) => (i === maxIdx || i === minIdx) ? 9 : 6);
const pointBorderWidths = data.map((_, i) => (i === maxIdx || i === minIdx) ? 3 : 2);

const width = 1000;
const height = 580;
const canvas = new ChartJSNodeCanvas({ width, height, backgroundColour: 'white' });

const config = {
  type: 'line',
  data: {
    labels,
    datasets: [{
      label: '월별 총 매출액',
      data,
      borderColor: '#2563EB',
      backgroundColor: 'rgba(37, 99, 235, 0.08)',
      pointBackgroundColor: pointColors,
      pointBorderColor: '#fff',
      pointBorderWidth: pointBorderWidths,
      pointRadius: pointRadii,
      pointHoverRadius: 10,
      borderWidth: 2.5,
      fill: true,
      tension: 0.3,
    }]
  },
  options: {
    plugins: {
      title: {
        display: true,
        text: '2024년 월별 매출 추이',
        font: { size: 20, weight: 'bold' },
        padding: { top: 10, bottom: 24 }
      },
      legend: { display: false },
    },
    scales: {
      x: {
        title: { display: true, text: '월', font: { size: 13 } },
        ticks: { font: { size: 12 } },
        grid: { color: 'rgba(0,0,0,0.06)' }
      },
      y: {
        title: { display: true, text: '총 매출액 (억 원)', font: { size: 13 } },
        ticks: {
          callback: v => v.toFixed(1) + '억',
          font: { size: 11 }
        },
        beginAtZero: false,
        suggestedMin: Math.min(...data) * 0.8,
        suggestedMax: Math.max(...data) * 1.2,
        grid: { color: 'rgba(0,0,0,0.06)' }
      }
    },
    layout: { padding: { top: 50, right: 30, bottom: 10, left: 10 } },
    animation: false
  },
  plugins: [{
    id: 'dataLabels',
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      chart.data.datasets.forEach((dataset, i) => {
        const meta = chart.getDatasetMeta(i);
        meta.data.forEach((point, idx) => {
          const value = dataset.data[idx];
          const isMax = idx === maxIdx;
          const isMin = idx === minIdx;
          const label = value.toFixed(2) + '억';

          // 수치 레이블
          ctx.save();
          ctx.font = `bold 11px sans-serif`;
          ctx.fillStyle = isMax ? '#E74C3C' : isMin ? '#E67E22' : '#2563EB';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'bottom';
          ctx.fillText(label, point.x, point.y - 12);
          ctx.restore();

          // 최고/최저 배지
          if (isMax || isMin) {
            const tag = isMax ? '▲ 최고' : '▼ 최저';
            const color = isMax ? '#E74C3C' : '#E67E22';
            const offsetY = isMax ? -32 : -32;

            ctx.save();
            ctx.font = 'bold 10px sans-serif';
            const tw = ctx.measureText(tag).width;
            const bx = point.x - tw / 2 - 6;
            const by = point.y + offsetY - 14;
            const bw = tw + 12;
            const bh = 16;
            const r = 4;

            // 배지 배경
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.moveTo(bx + r, by);
            ctx.lineTo(bx + bw - r, by);
            ctx.quadraticCurveTo(bx + bw, by, bx + bw, by + r);
            ctx.lineTo(bx + bw, by + bh - r);
            ctx.quadraticCurveTo(bx + bw, by + bh, bx + bw - r, by + bh);
            ctx.lineTo(bx + r, by + bh);
            ctx.quadraticCurveTo(bx, by + bh, bx, by + bh - r);
            ctx.lineTo(bx, by + r);
            ctx.quadraticCurveTo(bx, by, bx + r, by);
            ctx.closePath();
            ctx.fill();

            // 배지 텍스트
            ctx.fillStyle = '#fff';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(tag, point.x, by + bh / 2);
            ctx.restore();
          }
        });
      });
    }
  }]
};

(async () => {
  const buffer = await canvas.renderToBuffer(config);
  fs.writeFileSync('chart-line.png', buffer);
  console.log('저장 완료: chart-line.png');
  console.log('월별 매출:');
  sorted.forEach(([k, v]) => console.log(`  ${k}: ${(v / 100000000).toFixed(2)}억 원`));
})();
