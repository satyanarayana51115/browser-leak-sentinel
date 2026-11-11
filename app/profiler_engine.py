import asyncio
import os
import time
import pandas as pd
from playwright.async_api import async_playwright

METRICS_FILE = os.path.join(os.path.dirname(__file__), "..", "reports", "live_telemetry.csv")
TARGET_HTML = "file://" + os.path.abspath(os.path.join(os.path.dirname(__file__), "leaky_target.html"))

async def collect_cdp_metrics(cdp_session):
    """Query Chrome DevTools Protocol (CDP) for low-level memory and runtime performance metrics."""
    raw = await cdp_session.send("Performance.getMetrics")
    metrics = {m["name"]: m["value"] for m in raw["metrics"]}
    return {
        "timestamp": time.time(),
        "js_heap_used_mb": round(metrics.get("JSHeapUsedSize", 0) / (1024 * 1024), 2),
        "js_heap_total_mb": round(metrics.get("JSHeapTotalSize", 0) / (1024 * 1024), 2),
        "dom_nodes": int(metrics.get("Nodes", 0)),
        "js_event_listeners": int(metrics.get("JSEventListeners", 0)),
    }

async def run_profiler(iterations: int = 25, delay_per_step: float = 1.2):
    """Orchestrate Playwright browser automation and stream telemetry metrics to disk."""
    os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
    
    # Reset existing telemetry records for a fresh run
    if os.path.exists(METRICS_FILE):
        os.remove(METRICS_FILE)

    telemetry_records = []

    async with async_playwright() as p:
        # Launch headed chromium to provide visual demonstration during screen capture
        browser = await p.chromium.launch(headless=True, args=["--remote-debugging-port=9222"])
        page = await browser.new_page()
        
        # Initialize Chrome DevTools Protocol session
        cdp = await page.context.new_cdp_session(page)
        await cdp.send("Performance.enable")

        print(f"[*] Target Loaded: {TARGET_HTML}")
        await page.goto(TARGET_HTML)
        await asyncio.sleep(1)

        print(f"[*] Profiling initiated ({iterations} iterations)...")
        for step in range(1, iterations + 1):
            # Execute automated user interaction on the target app
            await page.click("#leakBtn")
            await asyncio.sleep(delay_per_step)

            # Record CDP metrics snapshot
            data = await collect_cdp_metrics(cdp)
            data["step"] = step
            telemetry_records.append(data)

            # Stream real-time telemetry to CSV for live dashboard consumption
            df = pd.DataFrame(telemetry_records)
            df.to_csv(METRICS_FILE, index=False)
            print(f"[Step {step:02d}/{iterations}] Heap Used: {data['js_heap_used_mb']} MB | DOM Nodes: {data['dom_nodes']}")

        print(f"[SUCCESS] Profiling completed. Telemetry exported to {METRICS_FILE}")
        await asyncio.sleep(1.5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_profiler())