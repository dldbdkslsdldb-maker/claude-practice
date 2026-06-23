const { ChartJSNodeCanvas } = require('chartjs-node-canvas');
const fs = require('fs');

const csv = fs.readFileSync('sales-data-clean.csv', 'utf-8');
const lines = csv.split('\n').filter(l => l.trim());
const headers = lines[0].split(',');
const regionIdx = headers.indexOf('지역');
const amtIdx = headers.indexOf('매출액');

const salesByRegion = {};
for (let i = 1; i < lines.length; i++) {
  const cols = lines[i].split(',');
  if (cols.length <= regionIdx) continue;
  const region = cols[regionIdx].trim();
  const amt = parseInt(cols[amtIdx], 10) || 0;
  salesByRegion[region] = (salesByRegion[region] || 0) + amt;
}

const sorted = Object.entries(salesByRegion).sort(([, a], [, b]) => b - a);
const labels = sorted.map(([k]) => k);
const data = sorted.map(([, v]) => v);
const total = data.reduce((s, v) => s + v, 0);

// 파란색 계열 색상 (진한 → 연한)
const colors = ['#1D4ED8', '#2563EB', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE'];

// 최고 비중 조각 분리 (index 0 = 서울)
const maxIdx = 0;
const offsets = data.map((_, i) => i === maxIdx ? 22 : 0);

const width = 860;
const height = 620;
const canvas = new ChartJSNodeCanvas({ width, height, backgroundColour: 'white' });

const config = {
  type: 'pie',
  data: {
    labels,
    datasets: [{
      data,
      backgroundColor: colors,
      borderColor: '#fff',
      borderWidth: 2,
      offset: offsets,
    }]
  },
  options: {
    plugins: {
      title: {
        display: true,
        text: '2024년 지역별 매출 비중',
        font: { size: 20, weight: 'bold' },
        padding: { top: 10, bottom: 20 }
      },
      legend: {
        display: true,
        position: 'right',
        labels: {
          font: { size: 13 },
          padding: 16,
          generateLabels: (chart) => {
            const ds = chart.data.datasets[0];
            return chart.data.labels.map((label, i) => {
              const val = ds.data[i];
              const pct = ((val / total) * 100).toFixed(1);
              return {
                text: `${label}  ${pct}%`,
                fillStyle: colors[i],
                strokeStyle: '#fff',
                lineWidth: 2,
                index: i,
              };
            });
          }
        }
      },
    },
    layout: { padding: { top: 20, right: 20, bottom: 20, left: 20 } },
    animation: false
  },
  plugins: [{
    id: 'pieLabels',
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      const meta = chart.getDatasetMeta(0);
      meta.data.forEach((arc, idx) => {
        const val = data[idx];
        const pct = ((val / total) * 100).toFixed(1);
        const regionName = labels[idx];

        // 조각 중심 좌표 (offset 반영)
        const angle = (arc.startAngle + arc.endAngle) / 2;
        const r = (arc.innerRadius + arc.outerRadius) / 2;
        const offsetDist = offsets[idx] || 0;
        const x = arc.x + Math.cos(angle) * (r + offsetDist * 0.5);
        const y = arc.y + Math.sin(angle) * (r + offsetDist * 0.5);

        ctx.save();
        // 지역명
        ctx.font = 'bold 13px sans-serif';
        ctx.fillStyle = '#fff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(regionName, x, y - 9);
        // 비율
        ctx.font = '12px sans-serif';
        ctx.fillText(`${pct}%`, x, y + 9);
        ctx.restore();
      });
    }
  }]
};

(async () => {
  const buffer = await canvas.renderToBuffer(config);
  fs.writeFileSync('chart-pie.png', buffer);
  console.log('저장 완료: chart-pie.png');
  console.log('지역별 매출:');
  sorted.forEach(([k, v]) => {
    const pct = ((v / total) * 100).toFixed(1);
    console.log(`  ${k}: ${(v / 100000000).toFixed(2)}억 원 (${pct}%)`);
  });
})();
