import csv
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from collections import defaultdict

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

sales_by_category = defaultdict(int)

with open('sales-data-clean.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        category = row['제품분류']
        amount = int(row['매출액'])
        sales_by_category[category] += amount

categories = list(sales_by_category.keys())
amounts = [sales_by_category[c] for c in categories]

sorted_pairs = sorted(zip(amounts, categories), reverse=True)
amounts, categories = zip(*sorted_pairs)

amounts_billion = [a / 1_000_000 for a in amounts]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(categories, amounts_billion, color=['#4C72B0', '#DD8452', '#55A868', '#C44E52'])

ax.set_title('제품분류별 총 매출액', fontsize=16, fontweight='bold', pad=15)
ax.set_xlabel('제품분류', fontsize=12)
ax.set_ylabel('총 매출액 (백만원)', fontsize=12)

for bar, val in zip(bars, amounts_billion):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            f'{val:,.1f}M', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax.set_ylim(0, max(amounts_billion) * 1.15)
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('sales_by_category.png', dpi=150, bbox_inches='tight')
print("저장 완료: sales_by_category.png")
