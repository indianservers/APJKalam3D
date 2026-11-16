"""Rebuild the accepted v5 sculpt from v4 using the frozen fit field.
Run in Blender. Saves a separate rebuilt file rather than replacing the master.
"""
import bpy,os
ROOT=r'C:\Abdul Kalam'
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'blender','apj_facial_v4_master.blend'))
for name in ['sculpt_likeness_v5.py','match_sculpt_v5_head_overlap.py','finish_likeness_v5.py','reference_expression_v5.py','apply_landmark_sculpt_v5.py','refresh_likeness_v5_rig.py']:
    path=os.path.join(ROOT,'scripts',name);exec(compile(open(path,encoding='utf-8').read(),name,'exec'))
LIKENESS_OUTPUT=os.path.join(ROOT,'blender','apj_likeness_v5_rebuilt.blend')
exec(compile(open(os.path.join(ROOT,'scripts','save_likeness_v5.py'),encoding='utf-8').read(),'save_likeness_v5.py','exec'))
