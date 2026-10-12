import json, sys
import fm_model, build_all
parts = fm_model.build()
res = build_all.export_stl(parts)
json.dump([[n, e] for p, n, e, w in res], open("out/img/stl_list.json", "w"))
print([ (n, w) for p, n, e, w in res if not w])
build_all.export_fbx(parts, f"{build_all.OUT}/filament_maker_assembly.fbx"); print("fbx ok")
