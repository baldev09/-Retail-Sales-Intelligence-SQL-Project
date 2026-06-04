import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3, os
np.random.seed(2025)

DB = '/home/claude/projects/sql_sales/data/retail_sales.db'
if os.path.exists(DB): os.remove(DB)
conn = sqlite3.connect(DB)

# ── 1. CUSTOMERS ─────────────────────────────
cities    = ['Mumbai','Pune','Bangalore','Delhi','Hyderabad','Chennai','Kolkata','Ahmedabad']
city_tier = {'Mumbai':'Tier-1','Pune':'Tier-1','Bangalore':'Tier-1','Delhi':'Tier-1',
             'Hyderabad':'Tier-1','Chennai':'Tier-1','Kolkata':'Tier-2','Ahmedabad':'Tier-2'}
city_p    = [0.20,0.15,0.18,0.16,0.12,0.10,0.05,0.04]

n_cust = 1000
cust_cities = np.random.choice(cities, n_cust, p=city_p)
customers = pd.DataFrame({
    'customer_id':  [f'CUST{str(i).zfill(4)}' for i in range(1, n_cust+1)],
    'customer_name':  [f'Customer_{i}' for i in range(1, n_cust+1)],
    'city':           cust_cities,
    'tier':           [city_tier[c] for c in cust_cities],
    'age_group':      np.random.choice(['18-25','26-35','36-45','46-60','60+'], n_cust,
                                        p=[0.15,0.30,0.25,0.20,0.10]),
    'gender':         np.random.choice(['M','F'], n_cust, p=[0.52,0.48]),
    'signup_date':    [(datetime(2021,1,1) + timedelta(days=int(d))).strftime('%Y-%m-%d')
                       for d in np.random.randint(0, 730, n_cust)]
})

# ── 2. PRODUCTS ──────────────────────────────
product_data = [
    ('PROD001','iPhone 15 Pro',     'Electronics',  'Apple',    89900, 72000),
    ('PROD002','Samsung Galaxy S24','Electronics',  'Samsung',  79999, 62000),
    ('PROD003','OnePlus 12',        'Electronics',  'OnePlus',  64999, 50000),
    ('PROD004','Boat Airdopes 141', 'Electronics',  'Boat',     1299,   700),
    ('PROD005','JBL Flip 6',        'Electronics',  'JBL',      9999,  6500),
    ('PROD006','Dell Laptop i5',    'Electronics',  'Dell',     55000, 42000),
    ('PROD007','HP Laser Printer',  'Electronics',  'HP',       15999, 11000),
    ('PROD008','Levi Jeans 511',    'Clothing',     'Levis',    3999,  1800),
    ('PROD009','Nike Air Max',      'Clothing',     'Nike',     8995,  5200),
    ('PROD010','Puma T-Shirt',      'Clothing',     'Puma',     999,    420),
    ('PROD011','Allen Solly Shirt', 'Clothing',     'Allen Solly',2499, 1100),
    ('PROD012','Prestige Cooker 5L','Home & Kitchen','Prestige',1895,   900),
    ('PROD013','Philips Air Fryer', 'Home & Kitchen','Philips', 6999,  4200),
    ('PROD014','Milton Flask 1L',   'Home & Kitchen','Milton',  599,    250),
    ('PROD015','Godrej Almirah',    'Furniture',    'Godrej',   18500, 11000),
    ('PROD016','Wipro LED Bulb pk', 'Home & Kitchen','Wipro',   499,    180),
    ('PROD017','Himalaya Face Wash','Beauty',       'Himalaya', 299,    100),
    ('PROD018','Lakme Foundation',  'Beauty',       'Lakme',    699,    280),
    ('PROD019','Mamaearth Serum',   'Beauty',       'Mamaearth',799,    320),
    ('PROD020','Classmate Notebook','Stationery',   'Classmate',199,     60),
    ('PROD021','Parker Pen Set',    'Stationery',   'Parker',   1199,   450),
    ('PROD022','Britannia Biscuits','FMCG',         'Britannia',60,      30),
    ('PROD023','Amul Butter 500g',  'FMCG',         'Amul',     290,    180),
    ('PROD024','Surf Excel 2kg',    'FMCG',         'HUL',      340,    200),
    ('PROD025','Tata Salt 1kg',     'FMCG',         'Tata',     28,      14),
]
products = pd.DataFrame(product_data,
    columns=['product_id','product_name','category','brand','price','cost'])

# ── 3. SALES REPS ────────────────────────────
reps = pd.DataFrame({
    'rep_id':     [f'REP{str(i).zfill(3)}' for i in range(1,21)],
    'rep_name':   [f'SalesRep_{i}' for i in range(1,21)],
    'region':     np.random.choice(['North','South','East','West'], 20),
    'target_monthly': np.random.choice([150000,200000,250000,300000], 20)
})

# ── 4. ORDERS ────────────────────────────────
n_orders = 12000
start = datetime(2023, 1, 1)
end   = datetime(2024, 12, 31)
days_range = (end - start).days

# seasonal multiplier — more sales in Oct-Dec (festive), Jan-Feb (winter)
def seasonal_weight(d):
    m = d.month
    return {1:1.1,2:0.9,3:0.85,4:0.80,5:0.85,6:0.90,
            7:0.95,8:1.0,9:1.1,10:1.4,11:1.5,12:1.3}.get(m,1.0)

raw_dates = [start + timedelta(days=int(d)) for d in np.random.randint(0, days_range, n_orders*2)]
weights   = np.array([seasonal_weight(d) for d in raw_dates])
weights   = weights / weights.sum()
idxs      = np.random.choice(len(raw_dates), n_orders, replace=False, p=weights)
order_dates = [raw_dates[i] for i in idxs]

# product popularity — electronics & FMCG sell more
prod_pop = {'Electronics':0.30,'Clothing':0.18,'Home & Kitchen':0.16,
            'FMCG':0.18,'Beauty':0.10,'Furniture':0.03,'Stationery':0.05}
cat_prods = {}
for _,row in products.iterrows():
    cat_prods.setdefault(row['category'],[]).append(row['product_id'])

def pick_product():
    cat = np.random.choice(list(prod_pop.keys()), p=list(prod_pop.values()))
    return np.random.choice(cat_prods[cat])

order_products = [pick_product() for _ in range(n_orders)]
prod_price = dict(zip(products['product_id'], products['price']))
prod_cost  = dict(zip(products['product_id'], products['cost']))

quantities = []
for pid in order_products:
    cat = products[products['product_id']==pid]['category'].values[0]
    if cat in ['Electronics','Furniture']:    q = np.random.choice([1,2], p=[0.90,0.10])
    elif cat == 'FMCG':                       q = np.random.randint(1,8)
    else:                                     q = np.random.randint(1,4)
    quantities.append(q)

discount_pct = np.random.choice([0,5,10,15,20,25,30], n_orders,
                                  p=[0.30,0.15,0.20,0.15,0.10,0.06,0.04])
unit_prices   = [prod_price[p] for p in order_products]
unit_costs    = [prod_cost[p]  for p in order_products]
gross_amounts = [up * q for up,q in zip(unit_prices, quantities)]
discount_amts = [ga * dp/100 for ga,dp in zip(gross_amounts, discount_pct)]
net_amounts   = [ga - da for ga,da in zip(gross_amounts, discount_amts)]
profits       = [(na - uc*q) for na,uc,q in zip(net_amounts, unit_costs, quantities)]

payment_modes = np.random.choice(['UPI','Credit Card','Debit Card','Net Banking','EMI','COD'],
                                   n_orders, p=[0.35,0.22,0.18,0.10,0.08,0.07])
statuses      = np.random.choice(['Delivered','Delivered','Delivered','Returned','Cancelled'],
                                   n_orders, p=[0.82,0.0,0.0,0.10,0.08])
# fix above
statuses = np.random.choice(['Delivered','Returned','Cancelled'], n_orders, p=[0.82,0.10,0.08])

orders = pd.DataFrame({
    'order_id':       [f'ORD{str(i).zfill(6)}' for i in range(1, n_orders+1)],
    'order_date':     [d.strftime('%Y-%m-%d') for d in order_dates],
    'customer_id':    np.random.choice(customers['customer_id'], n_orders),
    'product_id':     order_products,
    'rep_id':         np.random.choice(reps['rep_id'], n_orders),
    'quantity':       quantities,
    'unit_price':     unit_prices,
    'discount_pct':   discount_pct,
    'gross_amount':   [round(x,2) for x in gross_amounts],
    'discount_amount':[round(x,2) for x in discount_amts],
    'net_amount':     [round(x,2) for x in net_amounts],
    'profit':         [round(x,2) for x in profits],
    'payment_mode':   payment_modes,
    'order_status':   statuses,
    'year':           [d.year for d in order_dates],
    'month':          [d.month for d in order_dates],
    'quarter':        [f"Q{((d.month-1)//3)+1}" for d in order_dates],
})

# ── 5. WRITE TO SQLITE ───────────────────────
customers.to_sql('customers', conn, if_exists='replace', index=False)
products.to_sql('products',   conn, if_exists='replace', index=False)
reps.to_sql('sales_reps',     conn, if_exists='replace', index=False)
orders.to_sql('orders',       conn, if_exists='replace', index=False)

conn.execute("CREATE INDEX IF NOT EXISTS idx_order_date    ON orders(order_date)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_order_product ON orders(product_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_order_cust    ON orders(customer_id)")
conn.commit()
conn.close()

print("✅ Database created:", DB)
print(f"   customers  : {len(customers):,}")
print(f"   products   : {len(products):,}")
print(f"   sales_reps : {len(reps):,}")
print(f"   orders     : {len(orders):,}")
print(f"   Total GMV  : ₹{sum(net_amounts):,.0f}")
print(f"   Total Profit: ₹{sum(profits):,.0f}")
