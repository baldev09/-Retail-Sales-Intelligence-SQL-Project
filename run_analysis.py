"""
SQL Retail Sales Analysis — Output Runner
Executes every SQL query, prints results, saves charts
Author: Baldev Rathod
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

DB      = '/home/claude/projects/sql_sales/data/retail_sales.db'
OUTPUT  = '/home/claude/projects/sql_sales/outputs'
conn    = sqlite3.connect(DB)

sns.set_theme(style='whitegrid')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                     'axes.titleweight':'bold','figure.dpi':130})
BLUE  = '#1D4ED8'; GREEN = '#059669'; RED = '#DC2626'
GOLD  = '#D97706'; PURPLE= '#7C3AED'; TEAL = '#0891B2'
PALETTE = [BLUE, GREEN, RED, GOLD, PURPLE, TEAL, '#DB2777']

def fmt_inr(x, _): return f'₹{x/1e6:.1f}M' if x >= 1e6 else f'₹{x/1e3:.0f}K'

def run(sql): return pd.read_sql_query(sql, conn)

print("\n" + "="*65)
print("  RETAIL SALES INTELLIGENCE — SQL ANALYSIS")
print("  Author: Baldev Rathod | Pune")
print("="*65)

# ─── SECTION 1: OVERVIEW ──────────────────────────────────────
print("\n── SECTION 1: BUSINESS KPIs ──")
kpis = run("""
SELECT
    COUNT(DISTINCT order_id)                         AS total_orders,
    COUNT(DISTINCT customer_id)                      AS unique_customers,
    ROUND(SUM(net_amount),2)                         AS total_revenue,
    ROUND(SUM(profit),2)                             AS total_profit,
    ROUND(SUM(profit)*100.0/SUM(net_amount),2)       AS margin_pct,
    ROUND(AVG(net_amount),2)                         AS avg_order_value,
    SUM(quantity)                                    AS units_sold
FROM orders WHERE order_status='Delivered'
""")
for col in kpis.columns:
    print(f"  {col:<22}: {kpis[col].values[0]:>15,}")

# ─── MONTHLY TREND ─────────────────────────────────────────────
monthly = run("""
WITH m AS (
    SELECT strftime('%Y-%m',order_date) AS month,
           ROUND(SUM(net_amount),2) AS revenue,
           ROUND(SUM(profit),2)     AS profit,
           COUNT(order_id)          AS orders
    FROM orders WHERE order_status='Delivered'
    GROUP BY month
)
SELECT *, LAG(revenue) OVER (ORDER BY month) AS prev_rev,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY month))*100.0
          / NULLIF(LAG(revenue) OVER (ORDER BY month),0),2) AS mom_growth
FROM m ORDER BY month
""")
print(f"\n── SECTION 2: MONTHLY REVENUE (sample) ──")
print(monthly[['month','revenue','orders','mom_growth']].tail(8).to_string(index=False))

# ─── CATEGORY ──────────────────────────────────────────────────
category = run("""
SELECT p.category,
    COUNT(o.order_id)                                    AS orders,
    ROUND(SUM(o.net_amount),2)                           AS revenue,
    ROUND(SUM(o.profit),2)                               AS profit,
    ROUND(SUM(o.profit)*100.0/SUM(o.net_amount),2)       AS margin_pct,
    ROUND(SUM(o.net_amount)*100.0/SUM(SUM(o.net_amount)) OVER(),2) AS share_pct
FROM orders o JOIN products p ON o.product_id=p.product_id
WHERE o.order_status='Delivered'
GROUP BY p.category ORDER BY revenue DESC
""")
print(f"\n── SECTION 3: CATEGORY PERFORMANCE ──")
print(category.to_string(index=False))

# ─── TOP PRODUCTS ──────────────────────────────────────────────
top_prod = run("""
SELECT p.product_name, p.category, COUNT(o.order_id) AS orders,
    ROUND(SUM(o.net_amount),2) AS revenue,
    ROUND(SUM(o.profit)*100.0/SUM(o.net_amount),2) AS margin_pct
FROM orders o JOIN products p ON o.product_id=p.product_id
WHERE o.order_status='Delivered'
GROUP BY p.product_id ORDER BY revenue DESC LIMIT 10
""")
print(f"\n── SECTION 3: TOP 10 PRODUCTS ──")
print(top_prod.to_string(index=False))

# ─── CITY ──────────────────────────────────────────────────────
city = run("""
SELECT c.city, COUNT(DISTINCT c.customer_id) AS customers,
    COUNT(o.order_id) AS orders,
    ROUND(SUM(o.net_amount),2) AS revenue,
    ROUND(AVG(o.net_amount),2) AS avg_order_value
FROM orders o JOIN customers c ON o.customer_id=c.customer_id
WHERE o.order_status='Delivered'
GROUP BY c.city ORDER BY revenue DESC
""")
print(f"\n── SECTION 4: CITY-WISE REVENUE ──")
print(city.to_string(index=False))

# ─── DISCOUNT IMPACT ───────────────────────────────────────────
disc = run("""
SELECT
    CASE WHEN discount_pct=0 THEN '0% No Discount'
         WHEN discount_pct BETWEEN 1 AND 10 THEN '1-10%'
         WHEN discount_pct BETWEEN 11 AND 20 THEN '11-20%'
         ELSE '21%+' END AS discount_band,
    COUNT(order_id) AS orders,
    ROUND(SUM(net_amount),2) AS revenue,
    ROUND(SUM(profit)*100.0/SUM(net_amount),2) AS margin_pct
FROM orders WHERE order_status='Delivered'
GROUP BY discount_band ORDER BY MIN(discount_pct)
""")
print(f"\n── SECTION 6: DISCOUNT vs MARGIN ──")
print(disc.to_string(index=False))

# ─── SALES REP ─────────────────────────────────────────────────
reps = run("""
SELECT r.rep_name, r.region,
    COUNT(o.order_id) AS orders,
    ROUND(SUM(o.net_amount),2) AS revenue,
    ROUND(SUM(o.profit),2) AS profit,
    RANK() OVER (ORDER BY SUM(o.net_amount) DESC) AS rank
FROM orders o JOIN sales_reps r ON o.rep_id=r.rep_id
WHERE o.order_status='Delivered'
GROUP BY r.rep_id ORDER BY revenue DESC LIMIT 10
""")
print(f"\n── SECTION 5: TOP SALES REPS ──")
print(reps.to_string(index=False))

# ─── RETURNS ───────────────────────────────────────────────────
ret = run("""
SELECT order_status, COUNT(order_id) AS orders,
    ROUND(COUNT(order_id)*100.0/SUM(COUNT(order_id)) OVER(),2) AS pct
FROM orders GROUP BY order_status
""")
print(f"\n── SECTION 7: ORDER STATUS ──")
print(ret.to_string(index=False))

# ─── WINDOW FUNCTIONS ──────────────────────────────────────────
freq = run("""
WITH co AS (SELECT customer_id, COUNT(order_id) AS n FROM orders
             WHERE order_status='Delivered' GROUP BY customer_id)
SELECT
    CASE WHEN n=1 THEN '1 order'
         WHEN n BETWEEN 2 AND 4 THEN '2-4 orders'
         WHEN n BETWEEN 5 AND 9 THEN '5-9 orders'
         ELSE '10+ orders' END AS segment,
    COUNT(*) AS customers
FROM co GROUP BY segment ORDER BY MIN(n)
""")
print(f"\n── SECTION 8: PURCHASE FREQUENCY SEGMENTS ──")
print(freq.to_string(index=False))

# ═══════════════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════════════

# ── CHART 1: Revenue Dashboard ─────────────────────────────────
fig = plt.figure(figsize=(20, 14))
fig.suptitle('🛍️  Retail Sales Intelligence Dashboard — Baldev Rathod',
             fontsize=16, fontweight='bold', y=1.01)
gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.55, wspace=0.38)

# 1a — Monthly revenue bars + profit line
ax0 = fig.add_subplot(gs[0, :2])
x = range(len(monthly))
bars = ax0.bar(monthly['month'], monthly['revenue']/1e6,
               color=[BLUE if '2024' in m else TEAL for m in monthly['month']],
               alpha=0.85, edgecolor='white', label='Revenue')
ax2x = ax0.twinx()
ax2x.plot(monthly['month'], monthly['profit']/1e6, color=GREEN,
          linewidth=2.5, marker='o', markersize=4, label='Profit', zorder=5)
ax0.set_title('Monthly Revenue vs Profit (₹ Millions)')
ax0.set_ylabel('Revenue (₹M)'); ax2x.set_ylabel('Profit (₹M)')
ax0.tick_params(axis='x', rotation=55, labelsize=7)
handles1, _ = ax0.get_legend_handles_labels()
handles2, _ = ax2x.get_legend_handles_labels()
ax0.legend(handles1+handles2, ['Revenue','Profit'], loc='upper left', fontsize=9)

# 1b — Category pie
ax1 = fig.add_subplot(gs[0, 2])
wedges, texts, autotexts = ax1.pie(
    category['revenue'], labels=category['category'],
    autopct='%1.1f%%', startangle=90,
    colors=PALETTE[:len(category)],
    textprops={'fontsize':8})
ax1.set_title('Revenue Share by Category')

# 1c — Top 10 products bar
ax2 = fig.add_subplot(gs[1, :2])
ax2.barh(top_prod['product_name'][::-1], top_prod['revenue'][::-1]/1e6,
         color=PALETTE[:len(top_prod)][::-1], edgecolor='white')
ax2.set_title('Top 10 Products by Revenue (₹M)')
ax2.set_xlabel('Revenue (₹ Millions)')
ax2.tick_params(axis='y', labelsize=8)

# 1d — City revenue
ax3 = fig.add_subplot(gs[1, 2])
ax3.bar(city['city'], city['revenue']/1e6, color=PALETTE[:len(city)], edgecolor='white')
ax3.set_title('City-wise Revenue (₹M)')
ax3.set_ylabel('Revenue (₹M)')
ax3.tick_params(axis='x', rotation=30, labelsize=8)

# 1e — Discount vs Margin
ax4 = fig.add_subplot(gs[2, 0])
colors_d = [GREEN, GOLD, RED, '#7C3AED'][:len(disc)]
b = ax4.bar(disc['discount_band'], disc['margin_pct'], color=colors_d, edgecolor='white')
ax4.set_title('Profit Margin by Discount Band (%)')
ax4.set_ylabel('Margin %')
ax4.tick_params(axis='x', rotation=20, labelsize=8)
for bar in b:
    ax4.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2,
             f"{bar.get_height():.1f}%", ha='center', fontsize=8, fontweight='bold')

# 1f — Top reps
ax5 = fig.add_subplot(gs[2, 1])
top5 = reps.head(5)
ax5.barh(top5['rep_name'][::-1], top5['revenue'][::-1]/1e6,
         color=BLUE, edgecolor='white', alpha=0.85)
ax5.set_title('Top 5 Sales Reps by Revenue')
ax5.set_xlabel('Revenue (₹M)')
ax5.tick_params(axis='y', labelsize=9)

# 1g — Order status donut
ax6 = fig.add_subplot(gs[2, 2])
ax6.pie(ret['orders'], labels=ret['order_status'],
        autopct='%1.1f%%', startangle=90,
        colors=[GREEN, RED, GOLD][:len(ret)],
        wedgeprops={'width':0.55}, textprops={'fontsize':9})
ax6.set_title('Order Status Split')

plt.savefig(f'{OUTPUT}/01_sales_dashboard.png', bbox_inches='tight')
plt.close()
print(f"\n[CHART 1] Sales Dashboard saved.")

# ── CHART 2: Advanced SQL Insights ─────────────────────────────
fig2, axes = plt.subplots(2, 3, figsize=(20, 11))
fig2.suptitle('Advanced SQL Insights — Window Functions & Business Intelligence',
              fontsize=14, fontweight='bold')

# 2a — Running total
running = run("""
WITH m AS (SELECT strftime('%Y-%m',order_date) AS month,
           ROUND(SUM(net_amount),2) AS revenue
           FROM orders WHERE order_status='Delivered' GROUP BY month)
SELECT month, revenue,
    SUM(revenue) OVER (ORDER BY month) AS running_total
FROM m ORDER BY month
""")
axes[0,0].fill_between(range(len(running)), running['running_total']/1e6,
                        alpha=0.3, color=BLUE)
axes[0,0].plot(range(len(running)), running['running_total']/1e6,
               color=BLUE, linewidth=2)
axes[0,0].set_xticks(range(0, len(running), 3))
axes[0,0].set_xticklabels(running['month'][::3], rotation=45, fontsize=7)
axes[0,0].set_title('Cumulative Revenue Over Time (₹M)')
axes[0,0].set_ylabel('Cumulative Revenue (₹M)')

# 2b — 3-month rolling avg
rolling = run("""
WITH m AS (SELECT strftime('%Y-%m',order_date) AS month,
           ROUND(SUM(net_amount),2) AS revenue
           FROM orders WHERE order_status='Delivered' GROUP BY month)
SELECT month, revenue,
    ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),2) AS rolling3m
FROM m ORDER BY month
""")
axes[0,1].plot(range(len(rolling)), rolling['revenue']/1e6,
               color=TEAL, alpha=0.5, linewidth=1.5, label='Monthly')
axes[0,1].plot(range(len(rolling)), rolling['rolling3m']/1e6,
               color=BLUE, linewidth=2.5, label='3M Rolling Avg')
axes[0,1].set_xticks(range(0, len(rolling), 3))
axes[0,1].set_xticklabels(rolling['month'][::3], rotation=45, fontsize=7)
axes[0,1].set_title('3-Month Rolling Average Revenue (₹M)')
axes[0,1].legend(fontsize=9)

# 2c — Customer frequency segments
freq_colors = [TEAL, GOLD, GREEN, BLUE]
axes[0,2].bar(freq['segment'], freq['customers'],
              color=freq_colors[:len(freq)], edgecolor='white')
axes[0,2].set_title('Customer Purchase Frequency Segments')
axes[0,2].set_ylabel('Customers')
axes[0,2].tick_params(axis='x', rotation=15, labelsize=8)
for bar in axes[0,2].patches:
    axes[0,2].text(bar.get_x()+bar.get_width()/2, bar.get_height()+2,
                   str(int(bar.get_height())), ha='center', fontsize=9, fontweight='bold')

# 2d — QoQ growth
qoq = run("""
SELECT quarter,
    ROUND(SUM(CASE WHEN year=2023 THEN net_amount ELSE 0 END),2) AS rev_2023,
    ROUND(SUM(CASE WHEN year=2024 THEN net_amount ELSE 0 END),2) AS rev_2024
FROM orders WHERE order_status='Delivered' GROUP BY quarter ORDER BY quarter
""")
x_ = np.arange(len(qoq))
w  = 0.35
axes[1,0].bar(x_-w/2, qoq['rev_2023']/1e6, w, color=TEAL, label='2023', edgecolor='white')
axes[1,0].bar(x_+w/2, qoq['rev_2024']/1e6, w, color=BLUE, label='2024', edgecolor='white')
axes[1,0].set_xticks(x_); axes[1,0].set_xticklabels(qoq['quarter'])
axes[1,0].set_title('Quarterly Revenue: 2023 vs 2024 (₹M)')
axes[1,0].set_ylabel('Revenue (₹M)')
axes[1,0].legend()

# 2e — Payment mode
pay = run("""
SELECT payment_mode, COUNT(order_id) AS orders,
    ROUND(SUM(net_amount),2) AS revenue,
    ROUND(AVG(net_amount),2) AS avg_val,
    ROUND(SUM(CASE WHEN order_status='Returned' THEN 1.0 ELSE 0 END)*100/COUNT(*),2) AS return_rate
FROM orders GROUP BY payment_mode ORDER BY revenue DESC
""")
axes[1,1].bar(pay['payment_mode'], pay['revenue']/1e6,
              color=PALETTE[:len(pay)], edgecolor='white')
axes[1,1].set_title('Revenue by Payment Mode (₹M)')
axes[1,1].set_ylabel('Revenue (₹M)')
axes[1,1].tick_params(axis='x', rotation=20, labelsize=8)

# 2f — Pareto (80/20)
pareto = run("""
WITH pr AS (
    SELECT p.product_name,
           ROUND(SUM(o.net_amount),2) AS revenue
    FROM orders o JOIN products p ON o.product_id=p.product_id
    WHERE o.order_status='Delivered' GROUP BY p.product_id
)
SELECT product_name, revenue,
    ROUND(SUM(revenue) OVER (ORDER BY revenue DESC)*100.0/SUM(revenue) OVER(),2) AS cum_pct
FROM pr ORDER BY revenue DESC
""")
axes[1,2].bar(range(len(pareto)), pareto['revenue']/1e6,
              color=[BLUE if c <= 80 else RED for c in pareto['cum_pct']],
              edgecolor='white')
ax_p2 = axes[1,2].twinx()
ax_p2.plot(range(len(pareto)), pareto['cum_pct'],
           color=GOLD, linewidth=2.5, marker='o', markersize=3)
ax_p2.axhline(y=80, color=RED, linestyle='--', alpha=0.6, linewidth=1.5)
ax_p2.set_ylabel('Cumulative %')
axes[1,2].set_title('Product Revenue — Pareto (80/20 Rule)')
axes[1,2].set_xlabel('Products (ranked by revenue)')
axes[1,2].set_ylabel('Revenue (₹M)')
axes[1,2].set_xticks([])

plt.tight_layout()
plt.savefig(f'{OUTPUT}/02_advanced_sql_insights.png', bbox_inches='tight')
plt.close()
print(f"[CHART 2] Advanced SQL Insights saved.")

# ── EXPORT QUERY RESULTS TO CSV ────────────────────────────────
monthly.to_csv(f'{OUTPUT}/monthly_revenue.csv', index=False)
category.to_csv(f'{OUTPUT}/category_performance.csv', index=False)
top_prod.to_csv(f'{OUTPUT}/top_products.csv', index=False)
city.to_csv(f'{OUTPUT}/city_revenue.csv', index=False)
reps.to_csv(f'{OUTPUT}/sales_rep_performance.csv', index=False)

conn.close()

print(f"\n[OUTPUT] CSVs saved to {OUTPUT}/")
print("\n" + "="*65)
print("  BUSINESS IMPACT SUMMARY")
print("="*65)
print(f"  Total Revenue   : ₹{kpis['total_revenue'].values[0]/1e7:.2f} Crore")
print(f"  Total Profit    : ₹{kpis['total_profit'].values[0]/1e7:.2f} Crore")
print(f"  Profit Margin   : {kpis['margin_pct'].values[0]}%")
print(f"  Avg Order Value : ₹{kpis['avg_order_value'].values[0]:,.0f}")
print(f"  SQL Queries     : 30+ covering trends, products, customers, reps, returns")
print(f"  Window Functions: LAG, RANK, NTILE, SUM OVER, ROLLING AVG, RUNNING TOTAL")
print("="*65)
print("[DONE]\n")
