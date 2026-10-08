"""Pre-compute satellite observations for the demo fields into apps/api/demo_cache/."""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.stubble import service  # noqa: E402

DEMO_FIELDS = [
    {"type": "Point", "coordinates": [75.6816, 30.1613]},
]


def main() -> None:
    service.SEED_CACHE_DIR.mkdir(exist_ok=True)
    years = service.default_years()
    for geom_in in DEMO_FIELDS:
        geometry, _, _ = service._prepare_geometry(geom_in, 2.0)
        key = service._cache_key(geometry, years)
        obs = service.observe_field(geometry, years)
        src = service.CACHE_DIR / f"{key}.json"
        if not src.exists():
            print(f"{geom_in['coordinates']}: nothing cached (no clear scenes?)")
            continue
        shutil.copy(src, service.SEED_CACHE_DIR / f"{key}.json")
        burned = [h["year"] for h in obs["burn_history"] if h["status"] in service.BURN_STATUSES]
        print(f"{geom_in['coordinates']} -> {key}.json  burned seasons: {json.dumps(burned)}")


if __name__ == "__main__":
    main()
