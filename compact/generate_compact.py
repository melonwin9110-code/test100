#!/usr/bin/env python3
"""Standalone Python 3 generator; standard library only. Run in an empty output directory."""
import gzip, struct, math, random, json, collections
from pathlib import Path

W,H,D=129,88,129
PALETTE=['minecraft:air','minecraft:smooth_basalt','minecraft:stone','minecraft:calcite','minecraft:warped_hyphae','minecraft:moss_block']
DATA_VERSION=4671
rng=random.Random(9110)
blocks=bytearray(W*H*D)
def idx(x,y,z): return (y*D+z)*W+x
def put(x,y,z,b):
    if 0<=x<W and 0<=y<H and 0<=z<D: blocks[idx(x,y,z)]=b
def get(x,y,z):
    return blocks[idx(x,y,z)] if 0<=x<W and 0<=y<H and 0<=z<D else 0
def box(x0,y0,z0,x1,y1,z1,b):
    for y in range(y0,y1+1):
        for z in range(z0,z1+1):
            for x in range(x0,x1+1): put(x,y,z,b(x,y,z) if callable(b) else b)
def rock(x,y,z):
    n=rng.random()
    return 3 if n<.028 else 2 if n<.37 else 1
ground={}
# Broad mossy forest floor, with a steep terraced massif on the left.
for z in range(D):
    for x in range(W):
        h=3+int(1.3*math.sin(x*.09)+1.1*math.sin(z*.075))
        if x<40:
            hill=max(0, (39-x)*1.14 - max(0,z-48)*.25 + 3*math.sin(z*.045))
            h=max(h,3+int(hill//2)*2)
        ground[x,z]=h
        for y in range(h+1): put(x,y,z,5 if y==h else (1 if y<h-3 else 2))
# Raised sanctuary and a level path corridor to the rear.
for z in range(32,90):
    for x in range(39,96):
        if ((x-67)/30)**2+((z-61)/34)**2<1.05:
            box(x,0,z,x,9,z,2)
            put(x,9,z,5 if rng.random()<.32 else rock(x,9,z))
for z in range(17,111):
    for x in range(61,74):
        top=9 if z<=84 else max(3,9-(z-84)//3)
        box(x,0,z,x,top,z,2)
        put(x,top,z,1 if rng.random()<.3 else 2)
# Broad six-step entrance stair: 3-block treads, full blocks only.
for z in range(85,103):
    top=9-(z-85)//3
    half=15+(z-85)//6
    for x in range(67-half,68+half):
        box(x,0,z,x,top,z,2)
        put(x,top,z,1 if rng.random()<.65 else 2)
# Winding secondary paths, including a right-hand forest loop.
for z in range(10,122):
    cx=103+int(8*math.sin(z*.055))
    for x in range(cx-3,cx+4):
        h=ground[x,z]
        put(x,h,z,2 if rng.random()<.8 else 1)
for x in range(47,112):
    zc=110+int(3*math.sin(x*.09))
    for z in range(zc-3,zc+4):
        h=ground[x,z]; put(x,h,z,2)

def pillar(cx,cz,top,base=10,radius=2):
    box(cx-radius-1,base,cz-radius-1,cx+radius+1,base+2,cz+radius+1,rock)
    for y in range(base+3,top+1):
        rad=radius+1 if (y-base)%12 in (0,1) else radius
        for z in range(cz-rad,cz+rad+1):
            for x in range(cx-rad,cx+rad+1):
                # Chamfered corners and fluted faces.
                if abs(x-cx)==rad and abs(z-cz)==rad: continue
                if y>top-4 and ((x*19+z*7)%5 < y-(top-4)): continue
                put(x,y,z,rock(x,y,z))
    # Broken crowning fragments, individually supported.
    box(cx-1,top+1,cz-1,cx,top+2,cz,rock)

def arch(cx,cz,span,spring,rise,thickness=3,broken=False,axis='x'):
    # Rounded Gothic arch, built with 4-block-deep stone ribs.
    for u in range(-span,span+1):
        t=abs(u)/span
        outer=spring+round(rise*(1-t**1.5)**.65)
        for y in range(outer-thickness+1,outer+1):
            for dep in range(-2,3):
                if broken and u>2 and y>spring+rise-7: continue
                if broken and u>span-4 and y>outer-1: continue
                x,z=(cx+u,cz+dep) if axis=='x' else (cx+dep,cz+u)
                put(x,y,z,rock(x,y,z))

# Two tall portals with surviving longitudinal ribs form an open ruined nave.
for x,z,top in [(48,76,49),(86,76,47),(48,43,63),(86,43,59)]: pillar(x,z,top)
arch(67,76,19,44,20,4)
arch(67,43,19,57,19,4,True)
arch(48,59,16,46,17,3,False,'z')
arch(86,59,16,44,15,3,True,'z')
# Offset upper wall remnants with tall open window slits and a jagged skyline.
for x in range(46,90):
    cap=74+int(3*math.sin(x*1.3))+((x//4)%3)*2
    for y in range(62,cap):
        if 64<y<73 and x%9 in (2,3,4): continue
        if x>76 and y>69: continue
        if 58<x<65 and y>72: continue
        for z in range(40,43):
            if get(x,y,z) or y>68 or abs(x-48)<5 or abs(x-86)<5:
                put(x,y,z,rock(x,y,z))
# Pedestals and distinct shattered outer pillars, asymmetrical heights.
for x,z,top in [(32,79,38),(39,99,22),(99,75,43),(110,54,48),(99,35,36),(34,44,30),(91,98,27)]:
    base=max(ground[x,z]+1,10 if 39<x<96 and 32<z<90 else 5)
    pillar(x,z,top,base,1 if x==99 and z==35 else 2)
# Fallen masonry mostly outside the central passage.
for _ in range(100):
    x=rng.randrange(31,111); z=rng.randrange(29,104)
    if 58<=x<=77: continue
    y=max((yy for yy in range(24) if get(x,yy,z)),default=3)+1
    if y<19: box(x,y,z,x+rng.randrange(1,4),y+rng.randrange(0,2),z+rng.randrange(1,3),rock)
# Moss replaces exposed masonry and hangs from the surviving high ribs.
for y in range(10,80):
    for z in range(32,84):
        for x in range(40,94):
            if get(x,y,z) in (1,2) and get(x,y+1,z)==0:
                patch=math.sin(x*.31+z*.18)+math.sin(z*.39-y*.1)
                if patch>.6 and rng.random()<.65: put(x,y,z,5)
for x,z,length in [(52,76,10),(55,75,6),(80,76,8),(48,54,9),(49,59,6),(77,43,7),(85,48,5)]:
    tops=[y for y in range(38,73) if get(x,y,z)]
    if tops:
        top=max(tops)
        for y in range(top-length,top+1): put(x,y,z,5)

def line(a,b,mat=4):
    n=max(abs(b[i]-a[i]) for i in range(3))
    for j in range(n+1):
        p=tuple(round(a[i]+(b[i]-a[i])*j/max(1,n)) for i in range(3)); put(*p,mat)
def tree(x,z,height):
    # Entire tree, including broad stepped crown silhouettes, uses warped hyphae.
    base=max(y for y in range(H) if get(x,y,z))+1
    if base>28: return
    for y in range(base,base+height):
        put(x,y,z,4)
        if height>15: put(x+1,y,z,4)
    for k in range(5):
        angle=k*2.4+rng.random()*.6
        radius=rng.randrange(3,7)
        bx=x+round(math.cos(angle)*radius); bz=z+round(math.sin(angle)*radius)
        by=base+height-3-rng.randrange(0,6)
        line((x,by-4,z),(bx,by,bz))
        for dy in range(-1,3):
            rad=radius//2+2-(max(0,dy))
            for dz in range(-rad,rad+1):
                for dx in range(-rad,rad+1):
                    if abs(dx)+abs(dz)<=rad+1 and rng.random()>.10: put(bx+dx,by+dy,bz+dz,4)
centers=[]
for _ in range(600):
    x=rng.randrange(7,123); z=rng.randrange(7,123)
    if 38<x<97 and 26<z<107: continue
    if x<39: continue
    if abs(x-(103+int(8*math.sin(z*.055))))<7: continue
    if z>103 and 46<x<116: continue
    if any((x-a)**2+(z-b)**2<64 for a,b in centers): continue
    centers.append((x,z)); tree(x,z,rng.randrange(11,24))
# Smaller silhouette trees on the left foreground and terraces.
for x,z,h in [(22,108,15),(28,92,12),(20,63,13),(30,31,16),(16,19,15),(45,116,11)]: tree(x,z,h)
# Keep a continuous, 7-block-wide, 4-block-high walkable route through both portals.
route=[]
for z in range(18,112):
    floor=9 if z<=84 else max(3,9-(z-84)//3)
    for x in range(64,71):
        box(x,0,z,x,floor,z,2)
        box(x,floor+1,z,x,floor+4,z,0)
    route.append((67,floor+1,z))

# Compact edition: preserve vertical silhouette and resample the full footprint.
original_blocks=blocks
old_w,old_d=W,D
W,D=60,60
blocks=bytearray(W*H*D)
for y in range(H):
    for z in range(D):
        oz=min(old_d-1,int((z+.5)*old_d/D))
        for x in range(W):
            ox=min(old_w-1,int((x+.5)*old_w/W))
            put(x,y,z,original_blocks[(y*old_d+oz)*old_w+ox])
# Rebuild stair treads after compaction, keeping single-block rises.
for z in range(40,53):
    floor=max(3,9-(z-39)//2)
    for x in range(24,40):
        box(x,0,z,x,floor,z,2)
        box(x,floor+1,z,x,13,z,0)
        put(x,floor,z,1 if rng.random()<.55 else 2)
route=[]
for z in range(8,55):
    floor=9 if z<=39 else max(3,9-(z-39)//2)
    for x in range(29,34):
        box(x,0,z,x,floor,z,2)
        box(x,floor+1,z,x,floor+4,z,0)
    route.append((31,floor+1,z))

# Minimal complete NBT serializer. Litematica's packed states cross long boundaries.
def s(v):
    b=v.encode('utf8'); return struct.pack('>H',len(b))+b
def payload(t,v):
    if t==3: return struct.pack('>i',v)
    if t==4: return struct.pack('>q',v)
    if t==8: return s(v)
    if t==7: return struct.pack('>i',len(v))+bytes(v)
    if t==9:
        subtype,items=v; return bytes([subtype])+struct.pack('>i',len(items))+b''.join(payload(subtype,a) for a in items)
    if t==10: return b''.join(bytes([tt])+s(k)+payload(tt,vv) for k,(tt,vv) in v.items())+b'\0'
    if t==12: return struct.pack('>i',len(v))+b''.join(struct.pack('>Q',a & ((1<<64)-1)) for a in v)
    raise ValueError(t)
def save(name,root):
    root_name='Schematic' if str(name).endswith('.schem') else ''
    Path(name).write_bytes(gzip.compress(b'\x0a'+s(root_name)+payload(10,root),mtime=0))
def vec(x,y,z): return {k:(3,v) for k,v in zip(('x','y','z'),(x,y,z))}
states=[0]*((len(blocks)*3+63)//64)
for i,b in enumerate(blocks):
    off=i*3; word,shift=divmod(off,64)
    states[word]|=(b<<shift)&((1<<64)-1)
    if shift>61: states[word+1]|=b>>(64-shift)
count=sum(b!=0 for b in blocks)
region={'Position':(10,vec(0,0,0)),'Size':(10,vec(W,H,D)),
        'BlockStatePalette':(9,(10,[{'Name':(8,name)} for name in PALETTE])),
        'BlockStates':(12,states),'Entities':(9,(10,[])),'TileEntities':(9,(10,[])),
        'PendingBlockTicks':(9,(10,[])),'PendingFluidTicks':(9,(10,[]))}
meta={'Name':(8,'Overgrown Broken Sanctuary Compact'),'Author':(8,'OpenAI'),
      'Description':(8,'Five-block reference-inspired ruins, terraced left hillside, forest and broad entrance stair.'),
      'RegionCount':(3,1),'TimeCreated':(4,1793577600000),'TimeModified':(4,1793577600000),
      'TotalBlocks':(3,count),'TotalVolume':(3,len(blocks)),'EnclosingSize':(10,vec(W,H,D))}
save('overgrown_sanctuary_60x88x60.litematic',{'Version':(3,6),'SubVersion':(3,1),'MinecraftDataVersion':(3,DATA_VERSION),
      'Metadata':(10,meta),'Regions':(10,{'Sanctuary':(10,region)})})
# Sponge schematic v2: indices are unsigned VarInts (all palette values fit one byte).
schem={'Version':(3,2),'DataVersion':(3,DATA_VERSION),'Width':(2,W),'Height':(2,H),'Length':(2,D),
       'Offset':(11,[0,0,0]),'PaletteMax':(3,len(PALETTE)),
       'Palette':(10,{name:(3,i) for i,name in enumerate(PALETTE)}),
       'BlockData':(7,blocks),'BlockEntities':(9,(10,[])),'Entities':(9,(10,[])),
       'Metadata':(10,{'Name':(8,'Overgrown Broken Sanctuary Compact')})}
# Add the two remaining NBT types used by Sponge.
original_payload=payload
def payload(t,v):
    if t==2: return struct.pack('>h',v)
    if t==11: return struct.pack('>i',len(v))+b''.join(struct.pack('>i',a) for a in v)
    return original_payload(t,v)
save('overgrown_sanctuary_60x88x60.schem',schem)

# Independent NBT parsing and round-trip checks on the actual compressed files.
def read_nbt(path):
    data=gzip.decompress(Path(path).read_bytes()); pos=0
    def take(n):
        nonlocal pos
        b=data[pos:pos+n]; assert len(b)==n; pos+=n; return b
    def num(fmt): return struct.unpack(fmt,take(struct.calcsize(fmt)))[0]
    def string(): return take(num('>H')).decode('utf8')
    def read(t):
        if t in (2,3,4): return num({2:'>h',3:'>i',4:'>q'}[t])
        if t==8: return string()
        if t==7: return take(num('>i'))
        if t==9:
            subtype=num('>B'); return [read(subtype) for _ in range(num('>i'))]
        if t==10:
            out={}
            while True:
                tt=num('>B')
                if tt==0: return out
                name=string(); assert name not in out; out[name]=read(tt)
        if t in (11,12): return [num('>i' if t==11 else '>Q') for _ in range(num('>i'))]
        raise ValueError(t)
    assert num('>B')==10; string(); result=read(10); assert pos==len(data); return result
lit=read_nbt('overgrown_sanctuary_60x88x60.litematic'); reg=lit['Regions']['Sanctuary']
assert [v['Name'] for v in reg['BlockStatePalette']]==PALETTE
assert reg['Size']==dict(x=W,y=H,z=D)
decoded=bytearray(len(blocks))
for i in range(len(blocks)):
    word,shift=divmod(i*3,64); val=reg['BlockStates'][word]>>shift
    if shift>61: val|=reg['BlockStates'][word+1]<<(64-shift)
    decoded[i]=val&7
assert decoded==blocks
sp=read_nbt('overgrown_sanctuary_60x88x60.schem')
assert sp['BlockData']==blocks and sp['Palette']=={v:i for i,v in enumerate(PALETTE)}
assert (sp['Width'],sp['Height'],sp['Length'])==(W,H,D)
for x,y,z in route:
    for xx in range(x-2,x+3):
        assert get(xx,y-1,z)!=0
        assert all(get(xx,yy,z)==0 for yy in range(y,y+4))
for a,b in zip(route,route[1:]): assert abs(a[1]-b[1])<=1
counts=collections.Counter(blocks)
report={'dimensions':{'x':W,'y':H,'z':D},'minecraft_data_version':DATA_VERSION,
        'non_air_blocks':count,'palette_counts':{p:counts[i] for i,p in enumerate(PALETTE)},
        'validation':{'gzip_nbt_roundtrip':True,'litematica_all_packed_states_match':True,
                      'worldedit_all_blocks_match':True,'entrance_route_width':5,
                      'entrance_route_clearance':4,'entrance_route_length':len(route),
                      'max_route_step':1,'in_game_tested':False},
        'orientation':'Front is +Z; left slope is -X. Region minimum corner is (0,0,0).'}
Path('validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
