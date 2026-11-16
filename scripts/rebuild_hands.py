"""Connected quad hand reconstructions fitted to the APJ development rig.
Preserves the previous character as a hidden backup and saves a new project.
"""
import bpy,bmesh,math,os,json
import numpy as np
from mathutils import Vector
ROOT=r'C:\Abdul Kalam';OUT=os.path.join(ROOT,'textures','hands')
os.makedirs(OUT,exist_ok=True)
r=bpy.data.objects['Armature'];body=bpy.data.objects['char1']
if bpy.data.objects.get('APJ_Hand_Left'):
    raise RuntimeError('Hands already rebuilt; reopen the development master to rebuild')
bpy.context.scene.frame_set(1)
if r.animation_data:r.animation_data.action=None
if body.data.shape_keys.animation_data:body.data.shape_keys.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
for k in body.data.shape_keys.key_blocks:k.value=0

# Keep all original geometry and facial shape keys in a hidden backup.
backup=body.copy();backup.data=body.data.copy();backup.name='SOURCE_Before_Hand_Rebuild'
bpy.context.scene.collection.objects.link(backup);backup.hide_set(True);backup.hide_render=True
# Remove old exterior hands through the inner cuff; edit mode preserves facial keys.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
removed=len(body.data.vertices)
bpy.ops.mesh.bisect(plane_co=(.545,0,0),plane_no=(1,0,0),clear_outer=True,clear_inner=False,use_fill=False)
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bisect(plane_co=(-.545,0,0),plane_no=(-1,0,0),clear_outer=True,clear_inner=False,use_fill=False)
bpy.ops.object.mode_set(mode='OBJECT');removed-=len(body.data.vertices)

# UV atlas: five finger strips plus dorsal/palmar hand strips.
N=2048;rng=np.random.default_rng(7431)
yy,xx=np.mgrid[0:N,0:N].astype(np.float32);u=xx/(N-1);v=yy/(N-1)
def field(size,size_y=None):
    size_y=size if size_y is None else size_y
    src=rng.random((size_y+2,size+2)).astype(np.float32)
    x=u*size;y=v*size_y;ix=x.astype(np.int32);iy=y.astype(np.int32)
    fx=x-ix;fy=y-iy
    return (src[iy,ix]*(1-fx)*(1-fy)+src[iy,ix+1]*(fx)*(1-fy)+src[iy+1,ix]*(1-fx)*fy+src[iy+1,ix+1]*fx*fy)-.5
low=field(11,70);medium=field(75,600);fine=field(450,2048)
height=.003*fine+.005*medium
crease=np.zeros_like(u);pigment=np.zeros_like(u)
for row in range(5):
    lo=.015+row*.145;hi=lo+.128
    mask=(v>=lo)&(v<=hi);circ=(v-lo)/.128
    # Dorsal knuckle fans and multiple palmar flexion creases.
    dorsal=np.exp(-((circ-.625)/.20)**4)
    palmar=np.exp(-((circ-.125)/.18)**4)
    for center,width,amount in [(.36,.009,.33),(.66,.008,.27),(.11,.012,.16)]:
        line=center+.016*np.sin(circ*math.tau*2)+.004*medium
        main=np.exp(-((u-line)/width)**2)
        double=np.exp(-((u-line-.024)/(.005))**2)
        fold=(main*(dorsal*.34+palmar)+double*palmar*.24)*amount
        crease+=np.where(mask,fold,0)
        for offset in [-.018,.017]:
            small=np.exp(-((u-line-offset)/.0032)**2)*dorsal*.115
            crease+=np.where(mask,small,0)
    # Fine distal pad ridges are subtler than the joint creases.
    pad=np.exp(-((u-.87)/.12)**4)*palmar
    ridges=np.sin(340*np.sqrt((u-.96)**2+((circ-.125)*.7)**2))*.012*pad
    height+=np.where(mask,ridges,0)
    pigment+=np.where(mask,.035*dorsal+.025*np.exp(-((u-.36)/.07)**2),0)
# Broad curved palm folds, not a repetitive all-over bump.
palmmask=(v>.875);pv=(v-.88)/.11
for a,b,width in [(.34,.10,.008),(.53,-.13,.007),(.69,.09,.006)]:
    crease+=np.where(palmmask,np.exp(-((u-(a+b*np.sin(pv*math.pi)))/width)**2)*.20,0)
height-=crease*.07
base=np.zeros((N,N,3),np.float32);base[:]=(.67,.47,.345)
base+=low[:,:,None]*np.array([.065,.046,.035],np.float32)
base+=medium[:,:,None]*.018+fine[:,:,None]*.009
base-=pigment[:,:,None]*np.array([.5,.7,.7],np.float32)
base-=crease[:,:,None]*np.array([.15,.12,.095],np.float32)
base[palmmask]+=np.array([.052,.048,.039],np.float32)
# Scattered, low-contrast age spots with varied radius and opacity.
spots=np.zeros_like(u)
for i in range(74):
    cx,cy=rng.uniform(.08,.95),rng.uniform(.02,.99);rad=rng.uniform(.0018,.0055)
    spots+=np.exp(-(((u-cx)/rad)**2+((v-cy)/(rad*1.6))**2))*rng.uniform(.025,.10)
base-=spots[:,:,None]*np.array([.55,.68,.60],np.float32)
# Soft, irregular dorsal veins and mild pigmentation around metacarpals.
dorsalmask=(v>.755)&(v<.865)&(u>.12)&(u<.86)
dv=(v-.755)/.105
veins=np.zeros_like(u)
for a,phase in [(.24,0),(.62,1.5)]:
    curve=a+.055*np.sin(u*7+phase)
    veins+=np.exp(-((dv-curve)/.014)**2)*np.sin(np.clip((u-.12)/.74,0,1)*math.pi)
veins=np.where(dorsalmask,veins,0)
base-=veins[:,:,None]*np.array([.035,.008,-.002],np.float32)
height+=veins*.035
# Blender generated pixels are linear. Convert the artist's sRGB palette before saving.
base=np.where(base<=.04045,base/12.92,((base+.055)/1.055)**2.4)
rough=np.clip(.53+medium*.12+low*.06+crease*.12,.36,.73)
# Tangent normal uses physical scale approximations for the UV atlas regions.
gy,gx=np.gradient(height);normal=np.stack((-gx*80,-gy*12,np.ones_like(u)),axis=-1)
normal/=np.linalg.norm(normal,axis=-1,keepdims=True);normal=normal*.5+.5
def imagefile(name,array,color=True):
    im=bpy.data.images.new(name,width=N,height=N,alpha=False)
    if not color:im.colorspace_settings.name='Non-Color'
    rgba=np.ones((N,N,4),np.float32)
    rgba[:,:,:3]=array[:,:,None] if array.ndim==2 else array
    im.pixels.foreach_set(np.clip(rgba,0,1).ravel());im.filepath_raw=os.path.join(OUT,name+'.png');im.file_format='PNG';im.save();im.pack()
    return im
images={'color':imagefile('APJ_Hands_Albedo_2K',base),
 'roughness':imagefile('APJ_Hands_Roughness_2K',rough,False),
 'normal':imagefile('APJ_Hands_Normal_2K',normal,False),
 'height':imagefile('APJ_Hands_Height_2K',np.clip(.5+height,0,1),False)}
skin=bpy.data.materials.new('APJ_Aged_Hand_Skin');skin.use_nodes=True
nodes=skin.node_tree.nodes;links=skin.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Subsurface Weight'].default_value=.08;bs.inputs['Subsurface Scale'].default_value=.0012
bs.inputs['Subsurface Radius'].default_value=(1,.47,.25)
bs.inputs['IOR'].default_value=1.42
for typ,inputname in [('color','Base Color'),('roughness','Roughness')]:
    n=nodes.new('ShaderNodeTexImage');n.image=images[typ];links.new(n.outputs['Color'],bs.inputs[inputname])
n=nodes.new('ShaderNodeTexImage');n.image=images['normal'];nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.55;links.new(n.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs['Normal'])
nailmat=bpy.data.materials.new('APJ_Natural_Nail_Keratin');nailmat.use_nodes=True
nb=next(n for n in nailmat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
nb.inputs['Base Color'].default_value=(.21,.12,.09,1);nb.inputs['Roughness'].default_value=.40
nc=nailmat.node_tree.nodes.new('ShaderNodeVertexColor');nc.layer_name='Nail_Tint'
nailmat.node_tree.links.new(nc.outputs['Color'],nb.inputs['Base Color'])
nb.inputs['Subsurface Weight'].default_value=.05;nb.inputs['Subsurface Scale'].default_value=.0007
nb.inputs['Specular IOR Level'].default_value=.25
nb.inputs['Coat Weight'].default_value=.06;nb.inputs['Coat Roughness'].default_value=.40
nt=nailmat.node_tree.nodes.new('ShaderNodeTexNoise');nt.inputs['Scale'].default_value=160
bump=nailmat.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.10;bump.inputs['Distance'].default_value=.000025
nailmat.node_tree.links.new(nt.outputs['Fac'],bump.inputs['Height']);nailmat.node_tree.links.new(bump.outputs['Normal'],nb.inputs['Normal'])

# Four finger root slots across the palm, separated by small web strips.
starts=[0,5,10,15];names=['Index','Middle','Ring','Pinky']
yvals=[]
edges=[(-.030,-.010),(-.007,.014),(.017,.037),(.040,.058)]
for a,b in edges:
    yvals.extend(np.linspace(a,b,5).tolist())
# Indices 0..19: each slot spans 4 panels, gap occupies one panel.
NY=19;NX=9;NZ=4
xs=[.540,.551,.563,.575,.585,.595,.605,.615,.621,.626]
basez=1.303
fingerdata={
 'Index':{'x':.626,'y':-.020,'len':.080,'width':.0098,'thick':.0091},
 'Middle':{'x':.626,'y':.0035,'len':.090,'width':.0102,'thick':.0095},
 'Ring':{'x':.622,'y':.027,'len':.082,'width':.0096,'thick':.0089},
 'Pinky':{'x':.615,'y':.049,'len':.066,'width':.0082,'thick':.0076},
 'Thumb':{'x':.583,'y':-.023,'len':.069,'width':.0116,'thick':.0105}}
def jointpositions(f):return [0,.365,.68,1]
def center(f,t):
    d=fingerdata[f]
    if f=='Thumb':return Vector((d['x']+t*d['len']*.77,d['y']-t*d['len']*.64,basez-.007*t))
    return Vector((d['x']+t*d['len'],d['y']+(t*t)*(-.003 if f=='Pinky' else .001),basez-.006*t))
def basis(f):
    tangent=(center(f,1)-center(f,0)).normalized();across=Vector((-tangent.y,tangent.x,0)).normalized()
    up=tangent.cross(across).normalized();return tangent,across,up
def radius(f,t):
    d=fingerdata[f];taper=1-.24*t
    bulge=1+.065*math.exp(-((t-.365)/.065)**2)+.055*math.exp(-((t-.68)/.055)**2)
    tip=1 if t<.90 else math.sqrt(max(.015,1-((t-.90)/.105)**2))
    return d['width']*taper*bulge*tip,d['thick']*taper*bulge*tip

hands=[];nails=[]
for side,sign in [('Left',1),('Right',-1)]:
    verts=[];faces=[];uvfaces=[];weightsets=[];grid={};fingerindices={}
    def addvert(p,weights):
        i=len(verts);verts.append((sign*p[0],p[1],p[2]));weightsets.append(weights);return i
    def addface(indices,uv):
        faces.append(tuple(indices if sign==1 else list(reversed(indices))))
        uvfaces.append(uv if sign==1 else list(reversed(uv)))
    def palmuv(p,top=True):return ((p[0]-.535)/.10,.755+(p[1]+.04)/.11*.105 if top else .88+(p[1]+.04)/.11*.105)
    # Structured rounded palm, narrower under cuff and broader at the knuckles.
    for i in range(NX+1):
      for j in range(NY+1):
       for k in range(NZ+1):
        if i not in (0,NX) and j not in (0,NY) and k not in (0,NZ):continue
        t=i/NX;s=(yvals[j]-.014)/.044
        width=.48+.52*math.sin(t*math.pi*.5)
        y=.022+(yvals[j]-.022)*width
        x=xs[i]-(.009*(max(0,s)**1.8)+.001*max(0,-s))*t**4
        zz=(k/NZ*2-1);rounding=math.sqrt(max(.25,1-.50*abs(s)**5))
        z=basez+zz*(.0145-.0045*t)*rounding
        if k==NZ:
            z+=.0028*math.sin(math.pi*t)*math.cos(s*1.2)
            # Metacarpal tendon relief and MCP knuckle volumes.
            for fd in fingerdata.values():
                z+=.0008*math.exp(-((y-fd['y'])/.0045)**2)*math.sin(math.pi*t)
                z+=.0023*math.exp(-((x-(fd['x']-.007))/.008)**2-((y-fd['y'])/.008)**2)
        w={side+'Hand':1.}
        grid[i,j,k]=addvert((x,y,z),w)
    def quad(keys,uvtop=True):
        ids=[grid[a] for a in keys];uv=[palmuv(Vector((abs(verts[a][0]),verts[a][1],verts[a][2])),uvtop) for a in ids];addface(ids,uv)
    # Dorsal and palmar surfaces.
    for i in range(NX):
      for j in range(NY):
       quad([(i,j,NZ),(i+1,j,NZ),(i+1,j+1,NZ),(i,j+1,NZ)])
       quad([(i,j+1,0),(i+1,j+1,0),(i+1,j,0),(i,j,0)],False)
    for i in range(NX):
      for k in range(NZ):
       # Thumb opens into this side of the palm; it shares its root vertices.
       if i not in (3,4,5):quad([(i,0,k),(i+1,0,k),(i+1,0,k+1),(i,0,k+1)])
       quad([(i,NY,k+1),(i+1,NY,k+1),(i+1,NY,k),(i,NY,k)])
    for j in range(NY):
      for k in range(NZ):
       quad([(0,j,k),(0,j,k+1),(0,j+1,k+1),(0,j+1,k)])
       if j in (4,9,14):quad([(NX,j,k),(NX,j+1,k),(NX,j+1,k+1),(NX,j,k+1)])

    def skinweights(f,t):
        # Narrow, local transitions at joints avoid whole-finger rubber bending.
        if t<.03:return {side+'Hand':max(0,(.03-t)/.03),side+'Hand'+f+'1':min(1,t/.03)}
        for joint in [1,2]:
            q=jointpositions(f)[joint];half=.055
            if abs(t-q)<half:
                blend=(t-q+half)/(2*half);blend=blend*blend*(3-2*blend)
                return {f'{side}Hand{f}{joint}':1-blend,f'{side}Hand{f}{joint+1}':blend}
        seg=1 if t<.365 else 2 if t<.68 else 3
        return {f'{side}Hand{f}{seg}':1.}
    for row,f in enumerate(names+['Thumb']):
        if f!='Thumb':
            start=starts[names.index(f)]
            keys=[(NX,j,0) for j in range(start,start+5)]+[(NX,start+4,k) for k in range(1,5)]+[(NX,j,NZ) for j in range(start+3,start-1,-1)]+[(NX,start,k) for k in range(3,0,-1)]
        else:
            keys=[(i,0,0) for i in range(3,7)]+[(6,0,k) for k in range(1,5)]+[(i,0,NZ) for i in range(5,2,-1)]+[(3,0,k) for k in range(3,0,-1)]
        root=[grid[k] for k in keys];count=len(root)
        tangent,across,up=basis(f)
        # Root contour derives its angular correspondence from the existing palm.
        c=Vector((0,0,0))
        for ind in root:c+=Vector((abs(verts[ind][0]),verts[ind][1],verts[ind][2]))/count
        angles=[]
        for ind in root:
            p=Vector((abs(verts[ind][0]),verts[ind][1],verts[ind][2]))-c
            angles.append(math.atan2(p.dot(up)/.013,p.dot(across)/.010))
        ring=root;idsall=list(root)
        ts=[.025,.055,.10,.18,.26,.31,.34,.365,.39,.42,.49,.56,.62,.655,.68,.705,.735,.80,.86,.90,.94,.965,.985,1.0]
        for t in ts:
            ctr=center(f,t);rw,rh=radius(f,t);new=[]
            for angle in angles:
                # Compression-side crease and dorsal extensor knuckle contour.
                cs=math.cos(angle);sn=math.sin(angle)
                groove=sum(math.exp(-((t-q)/.010)**2) for q in [.365,.68])
                localr=1-.045*groove*max(0,-sn)
                p=ctr+across*(rw*cs*localr)+up*(rh*sn*localr)
                new.append(addvert(p,skinweights(f,t)))
            # Match circumference to the material atlas. A seam at ring wrap is UV only.
            oldt=ts[ts.index(t)-1] if ts.index(t)>0 else 0
            lo=.015+row*.145
            for a in range(count):
                b=(a+1)%count
                # angles need not be monotonic; normalized ring position is stable.
                va=lo+.128*a/count;vb=lo+.128*(a+1)/count
                addface([ring[a],new[a],new[b],ring[b]],[(oldt,va),(t,va),(t,vb),(oldt,vb)])
            ring=new;idsall.extend(new)
        # Small terminal quad fan, closing the rounded pad.
        tip=addvert(center(f,1.004),{side+'Hand'+f+'3':1})
        lo=.015+row*.145
        for a in range(count):addface([ring[a],tip,ring[(a+1)%count]],[(1,lo+.128*a/count),(1,lo+.064),(1,lo+.128*(a+1)/count)])
        fingerindices[f]=idsall
    mesh=bpy.data.meshes.new('APJ_'+side+'_Hand_QuadTopology');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new('APJ_Hand_'+side,mesh);bpy.context.scene.collection.objects.link(obj);obj.data.materials.append(skin)
    uv=mesh.uv_layers.new(name='Hand_Atlas')
    for poly,coords in zip(mesh.polygons,uvfaces):
        poly.use_smooth=True
        for li,coord in zip(poly.loop_indices,coords):uv.data[li].uv=coord
    groups={name:obj.vertex_groups.new(name=name) for name in sorted({n for w in weightsets for n in w})}
    for i,weights in enumerate(weightsets):
        for name,w in weights.items():
            if w>0:groups[name].add([i],w,'REPLACE')
    # Remove unused internal grid vertices (finger cap interiors).
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    arm=obj.modifiers.new('Finger deformation','ARMATURE');arm.object=r;arm.use_deform_preserve_volume=True
    sub=obj.modifiers.new('Hand surface refinement','SUBSURF');sub.levels=1;sub.render_levels=2
    obj.parent=r;obj['construction']='Connected quad palm and fingers, reconstructed anatomy';hands.append(obj)

    # Nail plates follow the distal phalanges, with curved surfaces and real thickness.
    for f in names+['Thumb']:
        tangent,across,up=basis(f);nv=[];nf=[]
        tc=.852;ctr=center(f,tc);rw,rh=radius(f,tc)
        length=.014 if f!='Pinky' else .011
        if f=='Thumb':length=.0145
        width=rw*.72
        # All-quad patch avoids a radial pole at the visible nail centre.
        for i in range(9):
            for j in range(9):
                a=i/8*2-1;b=j/8*2-1
                longitudinal=a*length*.5
                lateral=b*width*(1-.20*max(0,(abs(a)-.60)/.40)**2)
                t=tc+longitudinal/fingerdata[f]['len']
                trw,trh=radius(f,t)
                point=center(f,t)+across*lateral+up*(trh*math.sqrt(max(.1,1-(lateral/trw)**2))+.00020)
                nv.append((sign*point.x,point.y,point.z))
        for i in range(8):
            for j in range(8):
                inds=[i*9+j,(i+1)*9+j,(i+1)*9+j+1,i*9+j+1]
                nf.append(inds if sign==1 else list(reversed(inds)))
        nm=bpy.data.meshes.new(side+'_'+f+'_Nail');nm.from_pydata(nv,[],nf);nm.update()
        no=bpy.data.objects.new('APJ_Nail_'+side+'_'+f,nm);bpy.context.scene.collection.objects.link(no);nm.materials.append(nailmat)
        tint=nm.color_attributes.new(name='Nail_Tint',type='FLOAT_COLOR',domain='CORNER')
        for poly in nm.polygons:
            for li in poly.loop_indices:
                vi=nm.loops[li].vertex_index;i,j=divmod(vi,9);a=i/8;b=j/8
                free=max(0,min(1,(a-.91)/.09))
                lunula=math.exp(-((a-.09)/.15)**2-((b-.5)/.40)**2)*.22
                color=Vector((.21,.12,.09)).lerp(Vector((.43,.34,.25)),free*.72+lunula)
                tint.data[li].color=(*color,1)
        for p in nm.polygons:p.use_smooth=True
        ng=no.vertex_groups.new(name=side+'Hand'+f+'3');ng.add(list(range(len(nv))),1,'REPLACE')
        mod=no.modifiers.new('Distal phalanx binding','ARMATURE');mod.object=r
        sub=no.modifiers.new('Curved nail plate','SUBSURF');sub.levels=1;sub.render_levels=2
        thick=no.modifiers.new('Nail plate thickness','SOLIDIFY');thick.thickness=.00025
        no.parent=r;nails.append(no)

# Match joint heads to the reconstructed anatomy; original hand bones stay intact.
bpy.ops.object.select_all(action='DESELECT');r.select_set(True);bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for side,sign in [('Left',1),('Right',-1)]:
    for f in names+['Thumb']:
        qs=jointpositions(f)
        for j in range(3):
            bone=r.data.edit_bones[f'{side}Hand{f}{j+1}'];a=center(f,qs[j]);b=center(f,qs[j+1])
            bone.head=(sign*a.x,a.y,a.z);bone.tail=(sign*b.x,b.y,b.z);bone.align_roll(Vector((0,1,0)))
bpy.ops.object.mode_set(mode='OBJECT')
for o in hands+nails:o['revision']='Hands v2'
print(json.dumps({'hands':[o.name for o in hands],'nails':len(nails),'source_vertices_removed':removed,'textures':[im.filepath for im in images.values()]}))
