# Chicago Health Story Generator (Poster + Interactive Map + Story)
# -----------------------------------------------------------------

import os
from pathlib import Path
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import contextily as ctx
import folium

# ------------------------------------------------------------
# Paths (Your real directory)
# ------------------------------------------------------------
BASE = "/home/sam/projects/iitech/data_viz/mod9"

DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

# Data files as Path objects
GEO_PATH = Path(DATA) / "chicago-community-areas.geojson"
CSV_PATH = Path(DATA) / "public-health-statistics-selected-public-health-indicators-by-chicago-community-area-1.csv"

# Output files as Path objects
PNG_OUT = Path(OUT) / "chicago_health_poster.png"
HTML_OUT = Path(OUT) / "chicago_health_map.html"
BAR_OUT = Path(OUT) / "bar_top10.png"
HIST_OUT = Path(OUT) / "hist_metric.png"
TABLE_OUT = Path(OUT) / "table_top10.csv"
STORY_OUT = Path(OUT) / "story.html"

# ------------------------------------------------------------
# Load Data
# ------------------------------------------------------------
if not GEO_PATH.exists():
    raise FileNotFoundError(f"Missing GeoJSON: {GEO_PATH}")

if not CSV_PATH.exists():
    raise FileNotFoundError(f"Missing CSV: {CSV_PATH}")

geo = gpd.read_file(GEO_PATH)
df = pd.read_csv(CSV_PATH)

# ------------------------------------------------------------
# Select metric (you requested Low Birth Weight)
# ------------------------------------------------------------
metric = "Low Birth Weight"

if metric not in df.columns:
    raise ValueError(f'Column "{metric}" not found in CSV.')

# ------------------------------------------------------------
# Merge Data
# ------------------------------------------------------------
df["Community Area"] = df["Community Area"].astype(str)
geo["area_numbe"] = geo["area_numbe"].astype(str)

merged = geo.merge(df, left_on="area_numbe", right_on="Community Area", how="left")

# ------------------------------------------------------------
# PNG Poster Map (with numbers inside each region)
# ------------------------------------------------------------
fig, ax = plt.subplots(1, 1, figsize=(8, 10))
merged.plot(column=metric, cmap="Reds", linewidth=0.8, ax=ax, edgecolor="black", legend=True)
ctx.add_basemap(ax, crs=merged.crs.to_string(), source=ctx.providers.CartoDB.Positron)
ax.set_title(f"Chicago Health Metric: {metric}", fontsize=16)
ax.set_axis_off()

# Add numeric labels at the centroid of each area
for idx, row in merged.iterrows():
    if pd.notna(row[metric]):
        centroid = row['geometry'].centroid
        ax.text(
            centroid.x, centroid.y,
            f"{row[metric]:.1f}",
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=6,
            color='black',
            weight='bold'
        )

plt.savefig(PNG_OUT, dpi=300, bbox_inches="tight")
plt.close()

# ------------------------------------------------------------
# Interactive Map (HTML)
# ------------------------------------------------------------
m = folium.Map(location=[41.85, -87.65], zoom_start=10)

folium.Choropleth(
    geo_data=merged.to_json(),
    data=df,
    columns=["Community Area", metric],
    key_on="feature.properties.area_numbe",
    fill_color="YlOrRd",
    fill_opacity=0.8,
    line_opacity=0.4,
    legend_name=metric,
).add_to(m)

# Add tooltips with values
for idx, row in merged.iterrows():
    if pd.notna(row[metric]):
        folium.Marker(
            location=[row['geometry'].centroid.y, row['geometry'].centroid.x],
            icon=folium.DivIcon(
                html=f"""<div style="font-size: 10px; font-weight: bold; color: black;">{row[metric]:.1f}</div>"""
            )
        ).add_to(m)

m.save(HTML_OUT)

# ------------------------------------------------------------
# Additional Graphs
# ------------------------------------------------------------
top10 = df.nlargest(10, metric)
top10.to_csv(TABLE_OUT, index=False)

# Bar chart
plt.figure(figsize=(10, 6))
plt.barh(top10["Community Area"], top10[metric])
plt.gca().invert_yaxis()
plt.xlabel(metric)
plt.title(f"Top 10 Areas – {metric}")
plt.tight_layout()
plt.savefig(BAR_OUT, dpi=300)
plt.close()

# Histogram
plt.figure(figsize=(10, 6))
plt.hist(df[metric].dropna(), bins=20)
plt.xlabel(metric)
plt.ylabel("Frequency")
plt.title(f"Distribution of {metric}")
plt.tight_layout()
plt.savefig(HIST_OUT, dpi=300)
plt.close()

# ------------------------------------------------------------
# Story generation
# ------------------------------------------------------------
mean_val = df[metric].mean()
max_val = df[metric].max()
max_area = df.loc[df[metric] == max_val, "Community Area Name"].values[0]

story_html = f"""
<h1>Chicago Public Health Story – {metric}</h1>
<p>The map above highlights how the <strong>{metric}</strong> indicator varies across Chicago’s 77 community areas.</p>

<p>The citywide average is <strong>{mean_val:.2f}</strong>, but some communities face significantly higher challenges.</p>

<p>The highest value is found in <strong>{max_area}</strong>, reaching <strong>{max_val:.2f}</strong>.  
This suggests potential disparities in prenatal care, maternal health services, and overall socio-economic conditions.</p>

<p>The bar charts and histogram provide additional context, showing which neighborhoods are most affected and how this indicator is distributed across the city.</p>

<p>Use this story along with the poster and interactive map to support reporting, presentations, or policy discussion.</p>
"""

STORY_OUT.write_text(story_html)

print("All files generated successfully:")
print(f"- Poster PNG: {PNG_OUT}")
print(f"- Interactive Map: {HTML_OUT}")
print(f"- Bar Chart: {BAR_OUT}")
print(f"- Histogram: {HIST_OUT}")
print(f"- Table: {TABLE_OUT}")
print(f"- Story: {STORY_OUT}")
