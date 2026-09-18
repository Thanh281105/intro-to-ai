import argparse,shutil,zipfile
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--group-id',required=True); p.add_argument('--student-id',required=True); p.add_argument('--presentation',required=True); p.add_argument('--demo-url',required=True); a=p.parse_args(); root=Path(__file__).resolve().parents[1]; name=f'AI_midterm_{a.group_id}_{a.student_id}'; out=root/name; shutil.rmtree(out,ignore_errors=True); (out/'source').mkdir(parents=True); skip={'.venv','__pycache__','.git'}
for x in root.iterdir():
 if x.name not in {name,'experiments','.pytest_cache'} and x.name not in skip: shutil.copytree(x,out/'source'/x.name,dirs_exist_ok=True) if x.is_dir() else shutil.copy2(x,out/'source'/x.name)
shutil.copy2(a.presentation,out/'presentation.pdf'); (out/'demo.txt').write_text(a.demo_url+'\n',encoding='utf8')
zip_path=root/(name+'.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 for f in out.rglob('*'):
  if f.is_file(): z.write(f,f.relative_to(root))
print(zip_path)
