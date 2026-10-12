# DIY filament maker - Phase 1 foundation (generator)
Edit fm_params.py (all mm), then run with a Python that has bpy 5.x + trimesh + manifold3d + shapely:
  python build_all.py stl fbx exploded render:hero_all,hero_ext,drive,puller,spooler,die
  python fm_drawings.py ; python build_deck.py
fm_calc.py = throughput / die pressure / thrust numbers used on the sheets.
Items marked VERIFY are catalogue-typical sizes: confirm against the parts you buy.

## Rev B
- `fm_verify.py` checks the model: `python3 fm_verify.py [--rev-a] [--json out.json]` (needs trimesh, manifold3d, rtree, shapely).
- Rev B: 1 kg hopper (6.4 L, 60 degree cone, agitator), water bath, level-wind spooler. Result: 41 PASS, 1 WARN, 0 FAIL (Rev A: 18 FAIL).
- `rev_a/` keeps the Rev A generator for comparison. Everything follows `fm_params.py`.
