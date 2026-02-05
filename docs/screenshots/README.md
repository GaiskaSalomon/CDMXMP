# Screenshots Guide

## How to Capture Dashboard Screenshots

### Prerequisites
1. Run the dashboard: `make app`
2. Wait for it to load at http://localhost:8501
3. Use your browser's screenshot tool or a tool like:
   - **Windows**: Snipping Tool, Win + Shift + S
   - **Mac**: Cmd + Shift + 4
   - **Linux**: gnome-screenshot, Flameshot

### Required Screenshots

#### 1. `overview.png`
- Navigate to the **Overview** tab
- Ensure the map is visible with data points
- Show the KPI cards at the top
- Capture full screen or just the main content area
- **Target size**: ~1200x800 px, < 500 KB

#### 2. `executive_brief.png`
- Navigate to the **Executive Brief** tab
- Show the narrative insights and action items
- Include the KPI grid
- **Target size**: ~1200x800 px, < 500 KB

#### 3. `map_interactive.png`
- Navigate to the **Map** tab
- Toggle on the H3 heatmap layer
- Show points clustered in a high-density area
- Include the sidebar with filters
- **Target size**: ~1200x800 px, < 500 KB

#### 4. `accessibility.png`
- Navigate to the **Accessibility** tab
- Show the accessibility map with color-coded zones
- Include the ranking or percentile chart
- **Target size**: ~1200x800 px, < 500 KB

### Optional Screenshots

#### 5. `trends.png`
- Navigate to the **Trends** tab
- Show time-series charts
- Include filters applied (date range, hour)
- **Target size**: ~1200x800 px, < 500 KB

#### 6. `priority_index.png`
- Navigate to the **Priority Index** tab
- Show the PPI scores by zone
- Include the scatter plot (incidents vs exposure)
- **Target size**: ~1200x800 px, < 500 KB

### Tips for Good Screenshots

- ✅ Use **light mode** if dashboard supports it (or keep dark mode for consistency)
- ✅ **Zoom to 100%** in browser (avoid scaling artifacts)
- ✅ **Hide browser UI** (use fullscreen mode: F11 on Windows/Linux, Cmd+Shift+F on Mac)
- ✅ **Crop** to remove unnecessary whitespace
- ✅ **Optimize** images:
  ```bash
  # macOS/Linux
  convert overview.png -quality 85 -resize 1200x overview_optimized.png
  
  # Windows (with ImageMagick)
  magick overview.png -quality 85 -resize 1200x overview_optimized.png
  ```
- ✅ Use **descriptive filenames**: `overview.png`, not `screenshot1.png`

### After Capturing

1. Save images in this directory: `docs/screenshots/`
2. Verify file sizes (< 500 KB each)
3. The README already references these images
4. Commit to Git:
   ```bash
   git add docs/screenshots/*.png
   git commit -m "Add dashboard screenshots"
   ```

### Alternative: Use Streamlit Cloud

If you deploy to Streamlit Cloud, you can share the live URL instead of screenshots:
- Deploy: https://share.streamlit.io/
- Link in README: `[Live Demo](https://your-app.streamlit.app)`

---

**Current status**: 📸 Screenshots pending - follow this guide to add them!
