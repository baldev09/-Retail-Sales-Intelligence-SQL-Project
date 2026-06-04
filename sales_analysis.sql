-- ============================================================
-- RETAIL SALES INTELLIGENCE — SQL Analysis
-- Author  : Baldev Rathod | Data Analyst | Pune
-- Database: retail_sales.db (SQLite)
-- Tables  : orders, customers, products, sales_reps
-- ============================================================


-- ============================================================
-- SECTION 1: DATABASE OVERVIEW
-- ============================================================

-- Q1.1  How large is our dataset?
SELECT
    (SELECT COUNT(*) FROM orders)        AS total_orders,
    (SELECT COUNT(*) FROM customers)     AS total_customers,
    (SELECT COUNT(*) FROM products)      AS total_products,
    (SELECT COUNT(*) FROM sales_reps)    AS total_reps;

-- Q1.2  Business snapshot — key KPIs
SELECT
    COUNT(DISTINCT order_id)                            AS total_orders,
    COUNT(DISTINCT customer_id)                         AS unique_customers,
    ROUND(SUM(net_amount), 2)                           AS total_revenue,
    ROUND(SUM(profit), 2)                               AS total_profit,
    ROUND(SUM(profit) * 100.0 / SUM(net_amount), 2)    AS profit_margin_pct,
    ROUND(AVG(net_amount), 2)                           AS avg_order_value,
    SUM(quantity)                                       AS total_units_sold
FROM orders
WHERE order_status = 'Delivered';

-- Q1.3  Date range of data
SELECT
    MIN(order_date) AS first_order,
    MAX(order_date) AS last_order,
    COUNT(DISTINCT strftime('%Y-%m', order_date)) AS months_covered
FROM orders;


-- ============================================================
-- SECTION 2: REVENUE & SALES TRENDS
-- ============================================================

-- Q2.1  Monthly revenue trend (with MoM growth)
WITH monthly AS (
    SELECT
        strftime('%Y-%m', order_date)  AS ym,
        ROUND(SUM(net_amount), 2)       AS revenue,
        COUNT(order_id)                 AS orders
    FROM orders
    WHERE order_status = 'Delivered'
    GROUP BY ym
)
SELECT
    ym,
    revenue,
    orders,
    LAG(revenue) OVER (ORDER BY ym)                                     AS prev_month_revenue,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY ym)) * 100.0
        / NULLIF(LAG(revenue) OVER (ORDER BY ym), 0), 2)                AS mom_growth_pct
FROM monthly
ORDER BY ym;

-- Q2.2  Quarterly revenue comparison 2023 vs 2024
SELECT
    quarter,
    ROUND(SUM(CASE WHEN year = 2023 THEN net_amount ELSE 0 END), 2) AS revenue_2023,
    ROUND(SUM(CASE WHEN year = 2024 THEN net_amount ELSE 0 END), 2) AS revenue_2024,
    ROUND(
        (SUM(CASE WHEN year = 2024 THEN net_amount ELSE 0 END) -
         SUM(CASE WHEN year = 2023 THEN net_amount ELSE 0 END)) * 100.0
        / NULLIF(SUM(CASE WHEN year = 2023 THEN net_amount ELSE 0 END), 0), 2
    ) AS yoy_growth_pct
FROM orders
WHERE order_status = 'Delivered'
GROUP BY quarter
ORDER BY quarter;

-- Q2.3  Best and worst performing months
SELECT
    strftime('%Y-%m', order_date) AS month,
    ROUND(SUM(net_amount), 2)      AS revenue,
    RANK() OVER (ORDER BY SUM(net_amount) DESC) AS revenue_rank
FROM orders
WHERE order_status = 'Delivered'
GROUP BY month
ORDER BY revenue DESC;

-- Q2.4  Day-of-week sales pattern (which days sell most?)
SELECT
    CASE strftime('%w', order_date)
        WHEN '0' THEN 'Sunday'    WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'   WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'  WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END                            AS day_of_week,
    COUNT(order_id)                AS total_orders,
    ROUND(SUM(net_amount), 2)      AS total_revenue,
    ROUND(AVG(net_amount), 2)      AS avg_order_value
FROM orders
WHERE order_status = 'Delivered'
GROUP BY strftime('%w', order_date)
ORDER BY strftime('%w', order_date);


-- ============================================================
-- SECTION 3: PRODUCT PERFORMANCE
-- ============================================================

-- Q3.1  Top 10 products by revenue
SELECT
    p.product_name,
    p.category,
    p.brand,
    COUNT(o.order_id)              AS orders,
    SUM(o.quantity)                AS units_sold,
    ROUND(SUM(o.net_amount), 2)    AS total_revenue,
    ROUND(SUM(o.profit), 2)        AS total_profit,
    ROUND(SUM(o.profit) * 100.0 / SUM(o.net_amount), 2) AS margin_pct,
    RANK() OVER (ORDER BY SUM(o.net_amount) DESC) AS revenue_rank
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.order_status = 'Delivered'
GROUP BY p.product_id, p.product_name, p.category, p.brand
ORDER BY total_revenue DESC
LIMIT 10;

-- Q3.2  Category-wise performance breakdown
SELECT
    p.category,
    COUNT(o.order_id)                                    AS total_orders,
    SUM(o.quantity)                                      AS units_sold,
    ROUND(SUM(o.net_amount), 2)                          AS revenue,
    ROUND(SUM(o.profit), 2)                              AS profit,
    ROUND(SUM(o.profit) * 100.0 / SUM(o.net_amount), 2) AS margin_pct,
    ROUND(SUM(o.net_amount) * 100.0 /
          SUM(SUM(o.net_amount)) OVER (), 2)             AS revenue_share_pct
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.order_status = 'Delivered'
GROUP BY p.category
ORDER BY revenue DESC;

-- Q3.3  Products with declining sales (2023 → 2024)
WITH yearly AS (
    SELECT
        product_id,
        ROUND(SUM(CASE WHEN year = 2023 THEN net_amount ELSE 0 END), 2) AS rev_2023,
        ROUND(SUM(CASE WHEN year = 2024 THEN net_amount ELSE 0 END), 2) AS rev_2024
    FROM orders WHERE order_status = 'Delivered'
    GROUP BY product_id
)
SELECT
    p.product_name, p.category, y.rev_2023, y.rev_2024,
    ROUND((y.rev_2024 - y.rev_2023) * 100.0 / NULLIF(y.rev_2023, 0), 2) AS growth_pct
FROM yearly y
JOIN products p ON y.product_id = p.product_id
WHERE y.rev_2024 < y.rev_2023
ORDER BY growth_pct ASC;

-- Q3.4  Products never returned (reliable quality)
SELECT
    p.product_name, p.category,
    COUNT(o.order_id) AS total_orders,
    SUM(CASE WHEN o.order_status = 'Returned' THEN 1 ELSE 0 END) AS returns
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.product_id
HAVING returns = 0 AND total_orders > 50
ORDER BY total_orders DESC;


-- ============================================================
-- SECTION 4: CUSTOMER ANALYTICS
-- ============================================================

-- Q4.1  Customer lifetime value — top 20
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    c.age_group,
    COUNT(o.order_id)              AS total_orders,
    ROUND(SUM(o.net_amount), 2)    AS lifetime_value,
    ROUND(AVG(o.net_amount), 2)    AS avg_order_value,
    MIN(o.order_date)              AS first_order,
    MAX(o.order_date)              AS last_order,
    JULIANDAY(MAX(o.order_date)) - JULIANDAY(MIN(o.order_date)) AS customer_lifespan_days
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'Delivered'
GROUP BY c.customer_id
ORDER BY lifetime_value DESC
LIMIT 20;

-- Q4.2  City-wise revenue and average order value
SELECT
    c.city,
    c.tier,
    COUNT(DISTINCT c.customer_id)  AS customers,
    COUNT(o.order_id)              AS orders,
    ROUND(SUM(o.net_amount), 2)    AS revenue,
    ROUND(AVG(o.net_amount), 2)    AS avg_order_value,
    ROUND(SUM(o.net_amount) / COUNT(DISTINCT c.customer_id), 2) AS revenue_per_customer
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'Delivered'
GROUP BY c.city, c.tier
ORDER BY revenue DESC;

-- Q4.3  New vs returning customers per month
WITH customer_first AS (
    SELECT customer_id,
           MIN(strftime('%Y-%m', order_date)) AS first_month
    FROM orders GROUP BY customer_id
),
monthly_orders AS (
    SELECT
        strftime('%Y-%m', o.order_date) AS month,
        o.customer_id,
        cf.first_month
    FROM orders o
    JOIN customer_first cf ON o.customer_id = cf.customer_id
    WHERE o.order_status = 'Delivered'
)
SELECT
    month,
    COUNT(DISTINCT CASE WHEN month = first_month THEN customer_id END) AS new_customers,
    COUNT(DISTINCT CASE WHEN month > first_month  THEN customer_id END) AS returning_customers,
    COUNT(DISTINCT customer_id)                                          AS total_customers
FROM monthly_orders
GROUP BY month
ORDER BY month;

-- Q4.4  Customer retention: who bought in both 2023 and 2024?
SELECT
    COUNT(DISTINCT CASE WHEN year = 2023 THEN customer_id END) AS customers_2023,
    COUNT(DISTINCT CASE WHEN year = 2024 THEN customer_id END) AS customers_2024,
    COUNT(DISTINCT CASE WHEN year = 2023 THEN customer_id END) +
    COUNT(DISTINCT CASE WHEN year = 2024 THEN customer_id END) -
    COUNT(DISTINCT customer_id)                                  AS retained_customers,
    ROUND(
        (COUNT(DISTINCT CASE WHEN year = 2023 THEN customer_id END) +
         COUNT(DISTINCT CASE WHEN year = 2024 THEN customer_id END) -
         COUNT(DISTINCT customer_id)) * 100.0 /
        NULLIF(COUNT(DISTINCT CASE WHEN year = 2023 THEN customer_id END), 0), 2
    ) AS retention_rate_pct
FROM orders;

-- Q4.5  Age group buying behaviour
SELECT
    c.age_group,
    COUNT(DISTINCT o.customer_id)              AS customers,
    COUNT(o.order_id)                          AS orders,
    ROUND(AVG(o.net_amount), 2)                AS avg_order_value,
    p.category                                 AS top_category
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products  p ON o.product_id  = p.product_id
WHERE o.order_status = 'Delivered'
GROUP BY c.age_group, p.category
HAVING COUNT(o.order_id) = (
    SELECT MAX(cnt) FROM (
        SELECT c2.age_group, p2.category, COUNT(*) AS cnt
        FROM orders o2
        JOIN customers c2 ON o2.customer_id = c2.customer_id
        JOIN products  p2 ON o2.product_id  = p2.product_id
        WHERE o2.order_status = 'Delivered' AND c2.age_group = c.age_group
        GROUP BY c2.age_group, p2.category
    )
)
ORDER BY c.age_group;


-- ============================================================
-- SECTION 5: SALES REP PERFORMANCE
-- ============================================================

-- Q5.1  Sales rep leaderboard with target vs actual
SELECT
    r.rep_id,
    r.rep_name,
    r.region,
    r.target_monthly,
    COUNT(o.order_id)                              AS orders_closed,
    ROUND(SUM(o.net_amount), 2)                    AS total_revenue,
    ROUND(SUM(o.profit), 2)                        AS total_profit,
    ROUND(AVG(o.net_amount), 2)                    AS avg_deal_size,
    RANK() OVER (ORDER BY SUM(o.net_amount) DESC)  AS revenue_rank
FROM orders o
JOIN sales_reps r ON o.rep_id = r.rep_id
WHERE o.order_status = 'Delivered'
GROUP BY r.rep_id
ORDER BY total_revenue DESC;

-- Q5.2  Regional performance breakdown
SELECT
    r.region,
    COUNT(DISTINCT r.rep_id)           AS reps,
    COUNT(o.order_id)                  AS total_orders,
    ROUND(SUM(o.net_amount), 2)        AS revenue,
    ROUND(SUM(o.profit), 2)            AS profit,
    ROUND(AVG(o.net_amount), 2)        AS avg_order_value,
    ROUND(SUM(o.net_amount) * 100.0 /
          SUM(SUM(o.net_amount)) OVER (), 2) AS revenue_share_pct
FROM orders o
JOIN sales_reps r ON o.rep_id = r.rep_id
WHERE o.order_status = 'Delivered'
GROUP BY r.region
ORDER BY revenue DESC;

-- Q5.3  Top rep per region
WITH rep_revenue AS (
    SELECT
        r.rep_id, r.rep_name, r.region,
        ROUND(SUM(o.net_amount), 2) AS revenue,
        RANK() OVER (PARTITION BY r.region ORDER BY SUM(o.net_amount) DESC) AS region_rank
    FROM orders o
    JOIN sales_reps r ON o.rep_id = r.rep_id
    WHERE o.order_status = 'Delivered'
    GROUP BY r.rep_id, r.region
)
SELECT rep_id, rep_name, region, revenue
FROM rep_revenue
WHERE region_rank = 1
ORDER BY revenue DESC;


-- ============================================================
-- SECTION 6: DISCOUNT & PROFITABILITY ANALYSIS
-- ============================================================

-- Q6.1  How do discounts affect profit margin?
SELECT
    CASE
        WHEN discount_pct = 0          THEN '0% (No discount)'
        WHEN discount_pct BETWEEN 1 AND 10  THEN '1-10%'
        WHEN discount_pct BETWEEN 11 AND 20 THEN '11-20%'
        ELSE '21%+'
    END                                AS discount_band,
    COUNT(order_id)                    AS orders,
    ROUND(SUM(net_amount), 2)          AS revenue,
    ROUND(SUM(profit), 2)              AS profit,
    ROUND(SUM(profit)*100.0/SUM(net_amount), 2) AS margin_pct,
    ROUND(AVG(net_amount), 2)          AS avg_order_value
FROM orders
WHERE order_status = 'Delivered'
GROUP BY discount_band
ORDER BY MIN(discount_pct);

-- Q6.2  Categories with highest loss on heavy discounts
SELECT
    p.category,
    ROUND(AVG(o.discount_pct), 2)      AS avg_discount_pct,
    ROUND(SUM(o.discount_amount), 2)   AS total_discount_given,
    ROUND(SUM(o.profit), 2)            AS actual_profit,
    ROUND(SUM(o.profit + o.discount_amount), 2) AS potential_profit_without_discount
FROM orders o
JOIN products p ON o.product_id = p.product_id
WHERE o.order_status = 'Delivered' AND o.discount_pct > 15
GROUP BY p.category
ORDER BY total_discount_given DESC;

-- Q6.3  Payment mode performance
SELECT
    payment_mode,
    COUNT(order_id)               AS orders,
    ROUND(SUM(net_amount), 2)     AS revenue,
    ROUND(AVG(net_amount), 2)     AS avg_order_value,
    ROUND(AVG(discount_pct), 2)   AS avg_discount_pct,
    SUM(CASE WHEN order_status = 'Returned' THEN 1 ELSE 0 END)   AS returns,
    ROUND(SUM(CASE WHEN order_status = 'Returned' THEN 1 ELSE 0 END) * 100.0
          / COUNT(order_id), 2)                                    AS return_rate_pct
FROM orders
GROUP BY payment_mode
ORDER BY orders DESC;


-- ============================================================
-- SECTION 7: RETURN & CANCELLATION ANALYSIS
-- ============================================================

-- Q7.1  Order status breakdown
SELECT
    order_status,
    COUNT(order_id)                AS orders,
    ROUND(COUNT(order_id)*100.0 /
          SUM(COUNT(order_id)) OVER(), 2) AS pct_of_total,
    ROUND(SUM(net_amount), 2)      AS revenue_at_stake
FROM orders
GROUP BY order_status;

-- Q7.2  Categories with highest return rates
SELECT
    p.category,
    COUNT(o.order_id)              AS total_orders,
    SUM(CASE WHEN o.order_status = 'Returned'   THEN 1 ELSE 0 END) AS returns,
    SUM(CASE WHEN o.order_status = 'Cancelled'  THEN 1 ELSE 0 END) AS cancellations,
    ROUND(SUM(CASE WHEN o.order_status = 'Returned' THEN 1 ELSE 0 END)
          * 100.0 / COUNT(o.order_id), 2) AS return_rate_pct
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY return_rate_pct DESC;

-- Q7.3  Revenue lost to returns and cancellations per month
SELECT
    strftime('%Y-%m', order_date)  AS month,
    ROUND(SUM(CASE WHEN order_status = 'Returned'  THEN net_amount ELSE 0 END), 2) AS returned_value,
    ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN net_amount ELSE 0 END), 2) AS cancelled_value,
    ROUND(SUM(CASE WHEN order_status = 'Delivered' THEN net_amount ELSE 0 END), 2) AS delivered_value
FROM orders
GROUP BY month
ORDER BY month;


-- ============================================================
-- SECTION 8: ADVANCED WINDOW FUNCTION QUERIES
-- ============================================================

-- Q8.1  Running total revenue by month
SELECT
    strftime('%Y-%m', order_date)          AS month,
    ROUND(SUM(net_amount), 2)              AS monthly_revenue,
    ROUND(SUM(SUM(net_amount)) OVER
          (ORDER BY strftime('%Y-%m', order_date)), 2) AS running_total
FROM orders
WHERE order_status = 'Delivered'
GROUP BY month
ORDER BY month;

-- Q8.2  Customer purchase frequency buckets
WITH cust_orders AS (
    SELECT customer_id, COUNT(order_id) AS num_orders
    FROM orders WHERE order_status = 'Delivered'
    GROUP BY customer_id
)
SELECT
    CASE
        WHEN num_orders = 1       THEN 'One-time buyer'
        WHEN num_orders BETWEEN 2 AND 4 THEN '2-4 orders (Occasional)'
        WHEN num_orders BETWEEN 5 AND 9 THEN '5-9 orders (Regular)'
        ELSE '10+ orders (VIP)'
    END                              AS frequency_segment,
    COUNT(customer_id)               AS customers,
    ROUND(AVG(num_orders), 1)        AS avg_orders
FROM cust_orders
GROUP BY frequency_segment
ORDER BY MIN(num_orders);

-- Q8.3  Month-over-month revenue NTILE ranking (performance quartile)
WITH monthly_rev AS (
    SELECT
        strftime('%Y-%m', order_date) AS month,
        ROUND(SUM(net_amount), 2) AS revenue
    FROM orders WHERE order_status = 'Delivered'
    GROUP BY month
)
SELECT
    month, revenue,
    NTILE(4) OVER (ORDER BY revenue) AS performance_quartile,
    CASE NTILE(4) OVER (ORDER BY revenue)
        WHEN 4 THEN 'Top 25% — Excellent'
        WHEN 3 THEN 'Above Average'
        WHEN 2 THEN 'Below Average'
        ELSE 'Bottom 25% — Needs Attention'
    END AS performance_label
FROM monthly_rev
ORDER BY month;

-- Q8.4  Product revenue cumulative share (Pareto / 80-20 rule)
WITH prod_rev AS (
    SELECT
        p.product_name, p.category,
        ROUND(SUM(o.net_amount), 2) AS revenue
    FROM orders o JOIN products p ON o.product_id = p.product_id
    WHERE o.order_status = 'Delivered'
    GROUP BY p.product_id
),
cumulative AS (
    SELECT *,
        SUM(revenue) OVER (ORDER BY revenue DESC) AS cumulative_revenue,
        SUM(revenue) OVER ()                        AS total_revenue
    FROM prod_rev
)
SELECT
    product_name, category, revenue,
    ROUND(cumulative_revenue * 100.0 / total_revenue, 2) AS cumulative_pct,
    CASE WHEN cumulative_revenue * 100.0 / total_revenue <= 80
         THEN 'Top 80% Revenue' ELSE 'Tail 20%' END      AS pareto_group
FROM cumulative
ORDER BY revenue DESC;

-- Q8.5  3-month rolling average revenue (smoothed trend)
WITH monthly AS (
    SELECT
        strftime('%Y-%m', order_date) AS month,
        ROUND(SUM(net_amount), 2)      AS revenue
    FROM orders WHERE order_status = 'Delivered'
    GROUP BY month
)
SELECT
    month, revenue,
    ROUND(AVG(revenue) OVER (
        ORDER BY month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3m_avg
FROM monthly
ORDER BY month;


-- ============================================================
-- SECTION 9: BUSINESS SUMMARY DASHBOARD QUERY
-- ============================================================

-- Q9.1  Executive one-pager KPIs (single query)
SELECT
    'Total Revenue'     AS kpi, ROUND(SUM(net_amount),2)          AS value, '₹' AS unit
    FROM orders WHERE order_status='Delivered'
UNION ALL
SELECT 'Total Profit',   ROUND(SUM(profit),2),          '₹'  FROM orders WHERE order_status='Delivered'
UNION ALL
SELECT 'Profit Margin',  ROUND(SUM(profit)*100.0/SUM(net_amount),2), '%' FROM orders WHERE order_status='Delivered'
UNION ALL
SELECT 'Total Orders',   COUNT(order_id),                '#'  FROM orders WHERE order_status='Delivered'
UNION ALL
SELECT 'Avg Order Value',ROUND(AVG(net_amount),2),       '₹'  FROM orders WHERE order_status='Delivered'
UNION ALL
SELECT 'Unique Customers',COUNT(DISTINCT customer_id),  '#'  FROM orders WHERE order_status='Delivered'
UNION ALL
SELECT 'Return Rate',    ROUND(SUM(CASE WHEN order_status='Returned' THEN 1.0 ELSE 0 END)*100/COUNT(*),2),'%' FROM orders
UNION ALL
SELECT 'Cancel Rate',    ROUND(SUM(CASE WHEN order_status='Cancelled' THEN 1.0 ELSE 0 END)*100/COUNT(*),2),'%' FROM orders;
