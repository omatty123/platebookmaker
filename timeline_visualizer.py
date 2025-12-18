#!/usr/bin/env python3
"""
Google Timeline Visualizer (Online Tiles Version)
Author: @mahlernim
Uses online map tiles for crisp, detailed maps at any zoom level.

Requirements:
    pip install numpy matplotlib pillow python-dateutil requests

Tile providers:
    - CartoDB Light: https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png
    - CartoDB Dark: https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png
    - OpenStreetMap: https://tile.openstreetmap.org/{z}/{x}/{y}.png
"""

import json
import argparse
import os
import math
import hashlib
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PIL import Image
from matplotlib.animation import PillowWriter

try:
    import dateutil.parser
except ImportError:
    print("Missing dateutil. Run: pip install python-dateutil")
    exit(1)

try:
    import requests
except ImportError:
    print("Missing requests. Run: pip install requests")
    exit(1)

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
TILE_URL = "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
# Alternative tile URLs:
# TILE_URL = "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
# TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

CACHE_DIR = Path(".tile_cache")
TILE_SIZE = 256

# ------------------------------------------------------------
# Tile Functions
# ------------------------------------------------------------

def deg2num(lat_deg, lon_deg, zoom):
    """Convert lat/lon to tile numbers."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

def num2deg(xtile, ytile, zoom):
    """Convert tile numbers to lat/lon of NW corner."""
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg

def get_tile(x, y, z):
    """Fetch a tile, using cache if available."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{z}_{x}_{y}.png"
    
    if cache_file.exists():
        return Image.open(cache_file)
    
    url = TILE_URL.format(z=z, x=x, y=y)
    try:
        headers = {'User-Agent': 'TravelVisualizer/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img.save(cache_file)
        return img
    except Exception as e:
        print(f"Tile fetch error: {e}")
        return Image.new('RGB', (TILE_SIZE, TILE_SIZE), (240, 240, 240))

def get_map_for_bounds(min_lon, max_lon, min_lat, max_lat, width_px=1600):
    """Get a stitched map image for the given bounds."""
    # Calculate appropriate zoom level
    lon_span = max_lon - min_lon
    # Approximate: at zoom z, each tile covers 360/2^z degrees
    # We want enough tiles to fill width_px
    target_zoom = int(math.log2(360.0 / lon_span * width_px / TILE_SIZE))
    zoom = max(2, min(18, target_zoom))
    
    # Get tile range
    x_min, y_max = deg2num(min_lat, min_lon, zoom)
    x_max, y_min = deg2num(max_lat, max_lon, zoom)
    
    # Clamp to valid range
    n = 2 ** zoom
    x_min = max(0, x_min)
    x_max = min(n - 1, x_max)
    y_min = max(0, y_min)
    y_max = min(n - 1, y_max)
    
    # Calculate image size
    num_x = x_max - x_min + 1
    num_y = y_max - y_min + 1
    
    # Limit tiles to prevent huge downloads
    if num_x * num_y > 100:
        zoom -= 1
        return get_map_for_bounds(min_lon, max_lon, min_lat, max_lat, width_px)
    
    # Stitch tiles
    img_width = num_x * TILE_SIZE
    img_height = num_y * TILE_SIZE
    result = Image.new('RGB', (img_width, img_height))
    
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            tile = get_tile(x, y, zoom)
            px = (x - x_min) * TILE_SIZE
            py = (y - y_min) * TILE_SIZE
            result.paste(tile, (px, py))
    
    # Calculate actual bounds of stitched image
    nw_lat, nw_lon = num2deg(x_min, y_min, zoom)
    se_lat, se_lon = num2deg(x_max + 1, y_max + 1, zoom)
    
    extent = (nw_lon, se_lon, se_lat, nw_lat)
    return result, extent

# ------------------------------------------------------------
# Math Helpers
# ------------------------------------------------------------

def slerp(p0, p1, t):
    """Spherical Linear Interpolation between two points."""
    if np.allclose(p0, p1):
        return p0

    lon0, lat0 = np.radians(p0)
    lon1, lat1 = np.radians(p1)

    v0 = np.array([
        np.cos(lat0) * np.cos(lon0),
        np.cos(lat0) * np.sin(lon0),
        np.sin(lat0)
    ])
    v1 = np.array([
        np.cos(lat1) * np.cos(lon1),
        np.cos(lat1) * np.sin(lon1),
        np.sin(lat1)
    ])

    dot = np.clip(np.dot(v0, v1), -1.0, 1.0)
    omega = np.arccos(dot)

    if omega < 1e-6:
        return p0

    sin_omega = np.sin(omega)
    v_interp = (np.sin((1.0 - t) * omega) / sin_omega) * v0 + \
               (np.sin(t * omega) / sin_omega) * v1

    lat_interp = np.arcsin(v_interp[2])
    lon_interp = np.arctan2(v_interp[1], v_interp[0])

    return np.degrees(lon_interp), np.degrees(lat_interp)

# ------------------------------------------------------------
# Data Processing
# ------------------------------------------------------------

def parse_geo(s):
    if not s or not s.startswith("geo:"):
        return None
    try:
        lat, lon = s[4:].split(",")
        return float(lat), float(lon)
    except:
        return None

def extract_raw_points(data, target_year=2025):
    pts = []
    for seg in data:
        t0_str = seg.get("startTime")
        if not t0_str: continue
        t0 = dateutil.parser.parse(t0_str)
        if t0.year != target_year: continue
        
        t1_str = seg.get("endTime")
        t1 = dateutil.parser.parse(t1_str) if t1_str else t0

        # 1. visit
        visit = seg.get("visit", {})
        loc = visit.get("topCandidate", {}).get("placeLocation")
        p = parse_geo(loc)
        if p:
            pts.append({"time": t0, "lon": p[1], "lat": p[0]})

        # 2. activity
        activity = seg.get("activity", {})
        p_start = parse_geo(activity.get("start"))
        p_end = parse_geo(activity.get("end"))
        
        path_pts = activity.get("simplifiedRawPath", {}).get("points", [])
        if path_pts:
            num_pts = len(path_pts)
            total_delta = (t1 - t0).total_seconds()
            for i, pth in enumerate(path_pts):
                lat = pth.get("latE7") / 1e7
                lon = pth.get("lngE7") / 1e7
                offset = total_delta * ((i + 1) / (num_pts + 1))
                pt_time = t0 + timedelta(seconds=offset)
                pts.append({"time": pt_time, "lon": lon, "lat": lat})
        
        if p_start:
            pts.append({"time": t0, "lon": p_start[1], "lat": p_start[0]})
        if p_end:
            pts.append({"time": t1, "lon": p_end[1], "lat": p_end[0]})

        # 3. timelinePath
        for pth in seg.get("timelinePath", []):
            p = parse_geo(pth.get("point"))
            if p:
                offset = int(pth.get("durationMinutesOffsetFromStartTime", 0))
                pt_time = t0 + timedelta(minutes=offset)
                pts.append({"time": pt_time, "lon": p[1], "lat": p[0]})

    pts.sort(key=lambda x: x["time"])
    
    # Deduplicate
    clean = []
    if not pts: return clean
    
    clean.append(pts[0])
    for i in range(1, len(pts)):
        p_prev = clean[-1]
        p_curr = pts[i]
        if p_curr["lon"] == p_prev["lon"] and p_curr["lat"] == p_prev["lat"] and \
           (p_curr["time"] - p_prev["time"]).total_seconds() < 10:
            continue
        clean.append(p_curr)
    
    return clean

# ------------------------------------------------------------
# Pacing & Interpolation
# ------------------------------------------------------------

def prepare_animation_data(pts, total_frames):
    if not pts: return [], [], []

    real_times = np.array([(p["time"] - pts[0]["time"]).total_seconds() for p in pts])
    
    perceived_duration = [0]
    for i in range(1, len(pts)):
        p0 = (pts[i-1]["lon"], pts[i-1]["lat"])
        p1 = (pts[i]["lon"], pts[i]["lat"])
        dist = np.sqrt((p1[0]-p0[0])**2 + (p1[1]-p0[1])**2)
        move_weight = dist * 3.5
        time_weight = min((real_times[i] - real_times[i-1]) / 3600.0, 3.0)
        segment_weight = max(0.3, move_weight + time_weight)
        perceived_duration.append(perceived_duration[-1] + segment_weight)

    perceived_duration = np.array(perceived_duration)
    total_weight = perceived_duration[-1]
    
    frame_weights = np.linspace(0, total_weight, total_frames)
    
    path_lons = []
    path_lats = []
    frame_display_times = []

    for fw in frame_weights:
        idx = np.searchsorted(perceived_duration, fw)
        if idx == 0:
            p = (pts[0]["lon"], pts[0]["lat"])
            dt = pts[0]["time"]
        elif idx >= len(pts):
            p = (pts[-1]["lon"], pts[-1]["lat"])
            dt = pts[-1]["time"]
        else:
            w0, w1 = perceived_duration[idx-1], perceived_duration[idx]
            weight = (fw - w0) / (w1 - w0)
            p0 = (pts[idx-1]["lon"], pts[idx-1]["lat"])
            p1 = (pts[idx]["lon"], pts[idx]["lat"])
            
            dist = np.sqrt((p1[0]-p0[0])**2 + (p1[1]-p0[1])**2)
            if dist > 1.0:
                p = slerp(p0, p1, weight)
            else:
                lon = p0[0] + (p1[0] - p0[0]) * weight
                lat = p0[1] + (p1[1] - p0[1]) * weight
                p = (lon, lat)
            
            t0, t1 = real_times[idx-1], real_times[idx]
            rt = t0 + (t1 - t0) * weight
            dt = pts[0]["time"] + timedelta(seconds=rt)

        path_lons.append(p[0])
        path_lats.append(p[1])
        frame_display_times.append(dt)

    return np.array(path_lons), np.array(path_lats), frame_display_times

# ------------------------------------------------------------
# Main Visualization
# ------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="new2025.json")
    ap.add_argument("--output", default="trip_2025.mp4")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--duration", type=int, default=50)
    ap.add_argument("--dark", action="store_true", help="Use dark map tiles")
    args = ap.parse_args()

    # Set tile URL based on theme
    global TILE_URL
    if args.dark:
        TILE_URL = "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"

    print("Loading data...")
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_pts = extract_raw_points(data, target_year=args.year)
    if len(raw_pts) < 2:
        print("Not enough points found.")
        return

    total_frames = args.fps * args.duration
    lons, lats, times = prepare_animation_data(raw_pts, total_frames)

    print("Setting up plot...")
    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

    # Initial map (Wisconsin)
    init_img, init_extent = get_map_for_bounds(-93, -85, 42, 47)
    map_layer = ax.imshow(init_img, extent=init_extent, aspect='auto', zorder=0)

    # City labels
    cities = [
        # Wisconsin
        {"name": "Appleton", "lon": -88.41, "lat": 44.26},
        {"name": "Madison", "lon": -89.40, "lat": 43.07},
        {"name": "Menomonee Falls", "lon": -88.12, "lat": 43.18},
        {"name": "Door County", "lon": -87.15, "lat": 45.05},
        {"name": "The Cabin", "lon": -87.63, "lat": 45.10},
        # Korea
        {"name": "Seoul", "lon": 126.97, "lat": 37.56},
        {"name": "Suwon", "lon": 127.01, "lat": 37.26},
        {"name": "Gwangju", "lon": 126.85, "lat": 35.16},
        {"name": "Boseong", "lon": 127.08, "lat": 34.77},
        {"name": "Incheon", "lon": 126.45, "lat": 37.45}
    ]
    
    city_texts = []
    for city in cities:
        txt = ax.text(city["lon"], city["lat"] + 0.12, city["name"], color='white', 
                fontsize=10, fontweight='bold', ha='center', zorder=12,
                bbox=dict(facecolor='black', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2'))
        city_texts.append(txt)

    # Styling
    path_color = "#ff1e1e"
    glow_line, = ax.plot([], [], color="#ff0000", linewidth=15, alpha=0.15, zorder=4)
    main_line, = ax.plot([], [], color=path_color, linewidth=2.5, alpha=0.9, zorder=5)
    dot, = ax.plot([], [], 'o', color="white", markersize=16, markeredgecolor=path_color, 
                   markeredgewidth=3, zorder=20)

    date_text = ax.text(0.5, 0.94, "", transform=ax.transAxes, color="white", 
                        fontsize=36, fontweight='bold', ha='center',
                        bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.6'))

    # Initial view
    zoom_center = (-89.0, 44.2)
    zoom_width = 8.0
    ax.set_xlim(zoom_center[0] - zoom_width/2, zoom_center[0] + zoom_width/2)
    ax.set_ylim(zoom_center[1] - (zoom_width*9/16)/2, zoom_center[1] + (zoom_width*9/16)/2)

    # Track last map bounds to avoid re-fetching
    last_bounds = None

    def update(i):
        nonlocal last_bounds
        
        if i % 50 == 0:
            print(f"Frame {i}/{total_frames}...")
            
        k = i + 1
        x, y = lons[:k], lats[:k]
        
        # Mask jumps > 180 (Dateline crossing)
        diffs = np.abs(np.diff(x))
        mask = diffs > 180
        mx, my = np.array(x), np.array(y)
        if len(mask) > 0:
            indices = np.where(mask)[0] + 1
            mx = np.insert(mx, indices, np.nan)
            my = np.insert(my, indices, np.nan)

        main_line.set_data(mx, my)
        glow_line.set_data(mx, my)
        dot.set_data([lons[i]], [lats[i]])
        date_text.set_text(times[i].strftime("%B %d, %Y"))

        # Region-based stable camera
        curr_lon, curr_lat = lons[i], lats[i]
        
        # Define regions with fixed camera positions
        if -93 < curr_lon < -85 and 42 < curr_lat < 47:
            # Wisconsin region: center and width (higher width = more zoomed out)
            target_lon, target_lat, target_w = -89.0, 44.2, 8.0
        elif 124 < curr_lon < 130 and 33 < curr_lat < 39:
            # Korea region: set a smaller width for a tighter zoom
            target_lon, target_lat, target_w = 127.0, 36.0, 4.0
        else:
            target_lon, target_lat, target_w = curr_lon, curr_lat, 180.0
        
        # Removed cross-region lookahead trigger to allow camera to stay zoomed in until actually leaving the region
        
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        cw, clon, clat = (xlim[1]-xlim[0]), (xlim[0]+xlim[1])/2, (ylim[0]+ylim[1])/2
        
        if abs(target_lon - clon) > 180:
            clon += 360 if target_lon > clon else -360

        # Reduce lerp to slow down camera transitions and allow longer dwell
        lerp = 0.02
        nw = cw + (target_w - cw) * lerp
        nclon = clon + (target_lon - clon) * lerp
        nclat = clat + (target_lat - clat) * lerp
        
        aspect = 16/9
        new_xlim = (nclon - nw/2, nclon + nw/2)
        new_ylim = (nclat - (nw/aspect)/2, nclat + (nw/aspect)/2)
        
        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)
        
        # Update map tiles every 10 frames or when view changes significantly
        current_bounds = (round(new_xlim[0], 1), round(new_xlim[1], 1), 
                          round(new_ylim[0], 1), round(new_ylim[1], 1))
        
        if i % 10 == 0 or last_bounds != current_bounds:
            try:
                img, extent = get_map_for_bounds(new_xlim[0], new_xlim[1], 
                                                  new_ylim[0], new_ylim[1])
                map_layer.set_data(img)
                map_layer.set_extent(extent)
                last_bounds = current_bounds
            except Exception as e:
                print(f"Map update error: {e}")
        
        return main_line, glow_line, dot, date_text, map_layer

    print(f"Generating {total_frames} frames...")
    print("(First run will download tiles - subsequent runs use cache)")
    ani = animation.FuncAnimation(fig, update, frames=total_frames, blit=False)
    
    # Try using ffmpeg writer; fallback to PillowWriter if ffmpeg is unavailable
    try:
        writer = animation.FFMpegWriter(fps=args.fps, metadata=dict(artist='TravelVisualizer'), bitrate=8000)
        ani.save(args.output, writer=writer)
        print(f"Movie saved to {args.output}")
    except (FileNotFoundError, RuntimeError, OSError) as e:
        # Fallback to GIF using PillowWriter
        fallback_output = args.output
        # If output extension is mp4, change to gif
        base, ext = os.path.splitext(args.output)
        if ext.lower() != '.gif':
            fallback_output = base + '.gif'
        print(f"FFmpeg not found or failed ({e}); falling back to GIF output: {fallback_output}")
        writer = PillowWriter(fps=args.fps)
        ani.save(fallback_output, writer=writer)
        print(f"GIF saved to {fallback_output}")

if __name__ == "__main__":
    main()
