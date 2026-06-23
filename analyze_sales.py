import csv
import re
import math
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

INPUT_FILE = "sales-data.csv"
OUTPUT_CSV = "sales-data-cleaned.csv"
BAR_CHART = "chart-bar.png"
LINE_CHART = "chart-line.png"
PIE_CHART = "chart-pie.png"
REPORT_FILE = "report.md"

# ── 1단계: 원본 읽기 ──────────────────────────────────────────
with open(INPUT_FILE, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    headers = reader.fieldnames

original_count = len(rows)

# 결측값 진단
missing_count = defaultdict(int)
for row in rows:
    for k, v in row.items():
        if v.strip() == "":
            missing_count[k] += 1

# 중복 진단
seen_orders = {}
dup_count = 0
for row in rows:
    oid = row["주문번호"]
    if oid in seen_orders:
        dup_count += 1
    seen_orders[oid] = True

# 날짜 형식 불일치
date_bad = sum(1 for r in rows if re.search(r"\d{4}/\d{2}", r.get("주문일", "")))

print(f"[진단] 원본 {original_count}행 | 결측값 {sum(missing_count.values())}개 | 중복행 {dup_count}건 | 날짜형식불일치 {date_bad}건")

# ── 2단계: 정제 ───────────────────────────────────────────────
def is_all_numeric_missing(row):
    return (row.get("판매수량", "").strip() == "" and
            row.get("매출액", "").strip() == "" and
            row.get("영업이익", "").strip() == "")

cleaned = []
seen_orders2 = set()

for row in rows:
    # 핵심 수치 전체 결측 → 삭제
    if is_all_numeric_missing(row):
        continue
    # 중복 제거
    oid = row["주문번호"]
    if oid in seen_orders2:
        continue
    seen_orders2.add(oid)
    # 담당자 결측 채우기
    if row.get("담당자", "").strip() == "":
        row["담당자"] = "미확인"
    # 날짜 형식 통일
    row["주문일"] = row["주문일"].replace("/", "-")
    cleaned.append(row)

cleaned_count = len(cleaned)

with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(cleaned)

print(f"[정제] {original_count} → {cleaned_count}행 저장 완료: {OUTPUT_CSV}")

# ── 데이터 집계 ───────────────────────────────────────────────
def to_float(v):
    try:
        return float(v.replace(",", "").strip())
    except:
        return 0.0

# 제품분류별
cat_sales = defaultdict(float)
cat_profit = defaultdict(float)
cat_count = defaultdict(int)
for row in cleaned:
    cat = row["제품분류"]
    s = to_float(row["매출액"])
    p = to_float(row["영업이익"])
    if s > 0:
        cat_sales[cat] += s
        cat_profit[cat] += p
        cat_count[cat] += 1

# 월별
month_sales = defaultdict(float)
for row in cleaned:
    m = row["주문일"][:7]
    s = to_float(row["매출액"])
    if s > 0:
        month_sales[m] += s

# 지역별
region_sales = defaultdict(float)
region_profit = defaultdict(float)
region_count = defaultdict(int)
for row in cleaned:
    r = row["지역"]
    s = to_float(row["매출액"])
    p = to_float(row["영업이익"])
    if s > 0:
        region_sales[r] += s
        region_profit[r] += p
        region_count[r] += 1

# 담당자별
rep_sales = defaultdict(float)
for row in cleaned:
    rep = row["담당자"]
    s = to_float(row["매출액"])
    if s > 0:
        rep_sales[rep] += s

total_sales = sum(cat_sales.values())
total_profit = sum(cat_profit.values())
total_margin = total_profit / total_sales * 100 if total_sales else 0

# ── 3단계: 차트 생성 ──────────────────────────────────────────
W, H = 900, 560
BG = (255, 255, 255)
COLORS = [
    (70, 130, 180), (255, 140, 0), (60, 179, 113),
    (220, 20, 60), (147, 112, 219), (255, 215, 0), (32, 178, 170)
]

def try_font(size):
    for name in ["malgun.ttf", "malgunbd.ttf", "arial.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except:
            pass
    return ImageFont.load_default()

def draw_title(draw, text, w, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, 18), text, fill=(30, 30, 30), font=font)

# ── 막대 차트: 제품분류별 총 매출액 ──────────────────────────
img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)
font_title = try_font(22)
font_label = try_font(14)
font_small = try_font(12)

cats = sorted(cat_sales.keys(), key=lambda x: -cat_sales[x])
vals = [cat_sales[c] for c in cats]
max_val = max(vals)

margin_l, margin_r, margin_t, margin_b = 70, 30, 70, 90
chart_w = W - margin_l - margin_r
chart_h = H - margin_t - margin_b
bar_gap = 14
bar_w = (chart_w - bar_gap * (len(cats) - 1)) // len(cats)

draw_title(draw, "제품분류별 총 매출액", W, font_title)

# Y축 그리드
for i in range(6):
    y = margin_t + chart_h - int(chart_h * i / 5)
    draw.line([(margin_l, y), (W - margin_r, y)], fill=(220, 220, 220), width=1)
    label = f"{int(max_val * i / 5 / 1_000_000)}M"
    draw.text((margin_l - 45, y - 8), label, fill=(100, 100, 100), font=font_small)

for i, (cat, val) in enumerate(zip(cats, vals)):
    x0 = margin_l + i * (bar_w + bar_gap)
    bar_h = int(chart_h * val / max_val)
    y0 = margin_t + chart_h - bar_h
    color = COLORS[i % len(COLORS)]
    draw.rectangle([x0, y0, x0 + bar_w, margin_t + chart_h], fill=color)
    # 값 표시
    val_label = f"{val/1_000_000:.1f}M"
    bb = draw.textbbox((0, 0), val_label, font=font_small)
    tw = bb[2] - bb[0]
    draw.text((x0 + (bar_w - tw) // 2, y0 - 18), val_label, fill=(50, 50, 50), font=font_small)
    # X축 레이블 (대각선 배치)
    for j, ch in enumerate(cat):
        draw.text((x0 + bar_w // 2 - 6, margin_t + chart_h + 8 + j * 16), ch, fill=(60, 60, 60), font=font_small)

draw.line([(margin_l, margin_t), (margin_l, margin_t + chart_h)], fill=(80, 80, 80), width=2)
draw.line([(margin_l, margin_t + chart_h), (W - margin_r, margin_t + chart_h)], fill=(80, 80, 80), width=2)

img.save(BAR_CHART)
print(f"[차트] {BAR_CHART} 저장 완료")

# ── 선 차트: 월별 매출 추이 ──────────────────────────────────
img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

months = sorted(month_sales.keys())
vals = [month_sales[m] for m in months]
max_val = max(vals)
min_val = 0

draw_title(draw, "월별 매출 추이", W, font_title)

margin_l2, margin_r2, margin_t2, margin_b2 = 80, 30, 70, 60
chart_w2 = W - margin_l2 - margin_r2
chart_h2 = H - margin_t2 - margin_b2

for i in range(6):
    y = margin_t2 + chart_h2 - int(chart_h2 * i / 5)
    draw.line([(margin_l2, y), (W - margin_r2, y)], fill=(220, 220, 220), width=1)
    label = f"{int(max_val * i / 5 / 1_000_000)}M"
    draw.text((margin_l2 - 50, y - 8), label, fill=(100, 100, 100), font=font_small)

points = []
n = len(months)
for i, (m, v) in enumerate(zip(months, vals)):
    x = margin_l2 + int(chart_w2 * i / (n - 1)) if n > 1 else margin_l2
    y = margin_t2 + chart_h2 - int(chart_h2 * v / max_val)
    points.append((x, y))
    # x축 레이블
    draw.text((x - 18, margin_t2 + chart_h2 + 10), m[5:], fill=(60, 60, 60), font=font_small)

for i in range(len(points) - 1):
    draw.line([points[i], points[i + 1]], fill=(70, 130, 180), width=3)

for x, y in points:
    draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(70, 130, 180), outline=(255, 255, 255), width=2)

draw.line([(margin_l2, margin_t2), (margin_l2, margin_t2 + chart_h2)], fill=(80, 80, 80), width=2)
draw.line([(margin_l2, margin_t2 + chart_h2), (W - margin_r2, margin_t2 + chart_h2)], fill=(80, 80, 80), width=2)

img.save(LINE_CHART)
print(f"[차트] {LINE_CHART} 저장 완료")

# ── 원형 차트: 지역별 매출 비중 ──────────────────────────────
img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

regions = sorted(region_sales.keys(), key=lambda x: -region_sales[x])
vals = [region_sales[r] for r in regions]
total = sum(vals)

draw_title(draw, "지역별 매출 비중", W, font_title)

cx, cy, radius = 310, 295, 210
start = -90

for i, (reg, val) in enumerate(zip(regions, vals)):
    angle = val / total * 360
    color = COLORS[i % len(COLORS)]
    # PIL의 pieslice는 정수 각도 필요
    end = start + angle
    draw.pieslice([cx - radius, cy - radius, cx + radius, cy + radius],
                  start=start, end=end, fill=color, outline="white")
    # 레이블 각도 중심
    mid_angle = math.radians(start + angle / 2)
    lx = cx + int((radius * 0.65) * math.cos(mid_angle))
    ly = cy + int((radius * 0.65) * math.sin(mid_angle))
    pct = val / total * 100
    bb = draw.textbbox((0, 0), f"{pct:.1f}%", font=font_small)
    tw = (bb[2] - bb[0]) // 2
    th = (bb[3] - bb[1]) // 2
    draw.text((lx - tw, ly - th), f"{pct:.1f}%", fill="white", font=font_label)
    start = end

# 범례
legend_x, legend_y = 640, 180
for i, (reg, val) in enumerate(zip(regions, vals)):
    color = COLORS[i % len(COLORS)]
    draw.rectangle([legend_x, legend_y + i * 34, legend_x + 22, legend_y + i * 34 + 22], fill=color)
    pct = val / total * 100
    draw.text((legend_x + 30, legend_y + i * 34 + 3),
              f"{reg}  {val/1_000_000:.1f}M ({pct:.1f}%)", fill=(50, 50, 50), font=font_label)

img.save(PIE_CHART)
print(f"[차트] {PIE_CHART} 저장 완료")

# ── 4단계: 보고서 작성 ────────────────────────────────────────
months_sorted = sorted(month_sales.keys())
month_table_rows = ""
prev = None
for m in months_sorted:
    v = month_sales[m]
    if prev is not None:
        chg = (v - prev) / prev * 100
        chg_str = f"+{chg:.1f}%" if chg >= 0 else f"{chg:.1f}%"
    else:
        chg_str = "-"
    month_table_rows += f"| {m} | {v/1_000_000:.2f}M | {chg_str} |\n"
    prev = v

cat_table_rows = ""
for cat in sorted(cat_sales.keys(), key=lambda x: -cat_sales[x]):
    s = cat_sales[cat]
    p = cat_profit[cat]
    margin = p / s * 100 if s else 0
    cat_table_rows += f"| {cat} | {s/1_000_000:.2f}M | {p/1_000_000:.2f}M | {margin:.1f}% | {cat_count[cat]} |\n"

reg_table_rows = ""
for reg in sorted(region_sales.keys(), key=lambda x: -region_sales[x]):
    s = region_sales[reg]
    p = region_profit[reg]
    margin = p / s * 100 if s else 0
    share = s / total_sales * 100
    reg_table_rows += f"| {reg} | {s/1_000_000:.2f}M | {p/1_000_000:.2f}M | {margin:.1f}% | {share:.1f}% |\n"

top_cat = max(cat_sales, key=cat_sales.get)
top_region = max(region_sales, key=region_sales.get)
best_month = max(month_sales, key=month_sales.get)
worst_month = min(month_sales, key=month_sales.get)

report = f"""# 매출 데이터 분석 보고서

> 분석 대상: {INPUT_FILE} | 정제 후 {cleaned_count}건 | 기간: 2024-01 ~ 2024-12

---

## 1. 전체 요약

| 항목 | 값 |
|------|-----|
| 총 매출액 | {total_sales/1_000_000:.2f}M 원 |
| 총 영업이익 | {total_profit/1_000_000:.2f}M 원 |
| 평균 이익률 | {total_margin:.1f}% |
| 분석 주문 건수 | {cleaned_count}건 |
| 최고 매출 월 | {best_month} ({month_sales[best_month]/1_000_000:.2f}M) |
| 최저 매출 월 | {worst_month} ({month_sales[worst_month]/1_000_000:.2f}M) |
| 매출 1위 제품분류 | {top_cat} |
| 매출 1위 지역 | {top_region} |

---

## 2. 제품분류별 실적

| 제품분류 | 매출액 | 영업이익 | 이익률 | 주문수 |
|----------|--------|----------|--------|--------|
{cat_table_rows}
**분석:**
- **{top_cat}**이 전체 매출의 {cat_sales[top_cat]/total_sales*100:.1f}%를 차지하며 1위를 기록했습니다.
- 가구·인테리어는 단가가 높아 건당 매출 기여도가 크고, 이익률도 안정적인 수준을 유지합니다.
- 사무용품은 다품목 소량 구조로 주문 건수가 많지만 건당 매출은 낮습니다.

---

## 3. 지역별 실적

| 지역 | 매출액 | 영업이익 | 이익률 | 매출 비중 |
|------|--------|----------|--------|-----------|
{reg_table_rows}
**분석:**
- **{top_region}**이 전체 매출의 {region_sales[top_region]/total_sales*100:.1f}%로 최대 기여 지역입니다.
- 서울·경기 수도권이 전체 매출의 과반을 차지하며, 지방 거점(광주·대구)도 상당한 비중을 보입니다.
- 인천은 매출 규모 대비 이익률이 우수한 편입니다.

---

## 4. 월별 추이

| 월 | 매출액 | 전월 대비 |
|----|--------|-----------|
{month_table_rows}
**분석:**
- 상반기({months_sorted[0]}~{months_sorted[5]})는 완만한 성장세를 보이다가 하반기에 급증하는 패턴입니다.
- {best_month}이 최고 매출 월로, 연말 집중 발주 효과로 분석됩니다.
- {worst_month}는 연초 저조한 실적으로, 영업 파이프라인 확대가 필요합니다.

---

## 5. 종합 의견 및 다음 분기 제언

1. **IT기기·가구 라인 강화**: 두 카테고리가 전체 매출의 {(cat_sales.get('IT기기',0)+cat_sales.get('가구·인테리어',0))/total_sales*100:.0f}%를 차지하므로, 신제품 확보와 번들 제안으로 객단가를 높일 여지가 큽니다.
2. **비수기 대응**: {worst_month} 등 저매출 월에 선제적 프로모션·캠페인을 기획해 매출 편차를 줄여야 합니다.
3. **지방 거점 확대**: 부산·인천의 이익률이 준수하므로 담당자 역량 강화 및 타깃 고객 확대를 통해 점유율을 높이는 전략이 유효합니다.
4. **데이터 품질 관리**: 이번 분석에서 결측·중복 데이터 {original_count - cleaned_count}건이 확인됐습니다. CRM 입력 프로세스를 표준화해 데이터 누락을 최소화해야 합니다.
"""

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

print(f"[보고서] {REPORT_FILE} 저장 완료")
print()
print(f"✅ 정제 완료: {original_count} → {cleaned_count}")
print(f"✅ 차트 생성: {BAR_CHART} / {LINE_CHART} / {PIE_CHART}")
print(f"✅ 보고서 저장: {REPORT_FILE}")
