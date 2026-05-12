"""
generate_video.py
=================
Generate a national-resolution choropleth world map video from a World3 Extended
scenario run.  One frame is produced per simulation year, then assembled into an
MP4 (or GIF if ffmpeg is unavailable).

Usage
-----
  python scripts/generate_video.py [options]

Options
-------
  --config PATH         Path to YAML config file (default: config/default.yaml)
  --scenario NAME       Scenario module name (default: baseline)
  --output PATH         Output video path  (default: outputs/map_<scenario>.mp4)
  --frames-dir PATH     Directory to store PNG frames (default: outputs/frames_<scenario>)
  --fps INT             Frames per second in output video (default: 4)
  --keep-frames         Do not delete PNG frames after assembling video

The script must be run from the project root (world3_extended/) so that the
world3 package is importable.

Example
-------
  # Baseline
  python scripts/generate_video.py

  # Polycrisis at 6 fps, keep frames for inspection
  python scripts/generate_video.py --scenario polycrisis --fps 6 --keep-frames

NOTE: Outputs are exploratory scenario simulations only, not forecasts.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

# Ensure the project root is on the path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from world3.model import SimulationConfig, World3Model
from world3.utils.geomap import frames_to_video, generate_map_frames


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a world map time-series video from World3 Extended"
    )
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--frames-dir", default=None)
    parser.add_argument("--fps", type=int, default=4)
    parser.add_argument("--keep-frames", action="store_true")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    args = parse_args()
    cfg_path = Path(args.config)

    raw_cfg = World3Model.load_yaml(cfg_path)
    sim_cfg = SimulationConfig.from_mapping(raw_cfg)
    scenario_name = args.scenario or sim_cfg.scenario

    frames_dir = Path(args.frames_dir or f"outputs/frames_{scenario_name}")
    output_path = Path(args.output or f"outputs/map_{scenario_name}.mp4")

    logging.info("Running scenario '%s' for map generation...", scenario_name)
    model = World3Model(config=sim_cfg, raw_config=raw_cfg, scenario_name=scenario_name)
    df = model.run()

    logging.info("Generating %d map frames...", len(df))
    frame_paths = generate_map_frames(
        df=df,
        frames_dir=frames_dir,
        scenario_name=scenario_name,
    )
    logging.info("Generated %d frames in %s", len(frame_paths), frames_dir)

    logging.info("Assembling video → %s (fps=%d)", output_path, args.fps)
    final_path = frames_to_video(
        frame_paths=frame_paths,
        output_path=output_path,
        fps=args.fps,
    )

    if not args.keep_frames:
        shutil.rmtree(frames_dir, ignore_errors=True)
        logging.info("Removed frames directory %s", frames_dir)

    print(f"\nVideo written to: {final_path}")
    print("NOTE: These are exploratory scenario simulations only, not forecasts.")


if __name__ == "__main__":
    main()
