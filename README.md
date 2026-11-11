# Fisher

Search a lake by name, see its outline on satellite imagery. This is the base for an
any-lake fish-habitat prediction app (see the project handoff doc for the roadmap).

## Run it

Needs Python 3 and Node 18+.

    ./setup.sh     # once: creates backend/.venv, installs everything, runs the tests
    ./run.sh       # starts backend (8000) and frontend (5173)

Then open http://localhost:5173 and search a lake.

## Manual commands (if you prefer)

    cd backend
    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
    .venv/bin/python -m pytest -q
    .venv/bin/python -m uvicorn main:app --reload      # http://localhost:8000/api/health

    cd frontend
    npm install
    npm run dev

## Layout

    backend/    FastAPI. GET /api/lakes/search?q=...  (OpenStreetMap Nominatim, cached 1 h)
    frontend/   React + Vite + Leaflet. /api is proxied to the backend in dev.
    scripts/    inspect_service.py: checks the MN DNR bathymetry service schema.

## Test checklist for this step

Search these and confirm the outline looks right on the satellite view:
a small pond, a lake with islands, an ambiguous name ("Long Lake"), a big lake, a typo.
