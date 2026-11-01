#!/usr/bin/env python3
"""Reference-led compact ruined sanctuary. Python 3 standard library only."""
import gzip, struct, math, random, json, collections
from pathlib import Path

W,H,D=60,88,60
DATA_VERSION=4671
PALETTE=['minecraft:air','minecraft:smooth_basalt','minecraft:stone','minecraft:calcite','minecraft:warped_hyphae','minecraft:moss_block']
blocks=bytearray(W*H*D)
rng=random.Random(911002)
def idx(x,y,z): return (y*D+z)*W+x
def put(x,y,z,b):
    if 0<=x<W and 0<=y<H and 0<=z<D: blocks[idx(x,y,z)]=b
def get(x,y,z):
    return blocks[idx(x,y,z)] if 0<=x<W and 0<=y<H and 0<=z<D else 0
def box(x0,y0,z0,x1,y1,z1,b):
    for y in range(y0,y1+1):
        for z in range(z0,z1+1):
            for x in range(x0,x1+1): put(x,y,z,b(x,y,z) if callable(b) else b)
def hashed(x,z,seed=0):
    n=(x*374761393+z*668265263+seed*1274126177)&0xffffffff
    n=((n^(n>>13))*1274126177)&0xffffffff
    return ((n^(n>>16))&0xffff)/65535
def noise(x,z,seed=0):
    ix,iz=math.floor(x),math.floor(z); fx,fz=x-ix,z-iz
    fx=fx*fx*(3-2*fx); fz=fz*fz*(3-2*fz)
    return ((1-fx)*hashed(ix,iz,seed)+fx*hashed(ix+1,iz,seed))*(1-fz)+((1-fx)*hashed(ix,iz+1,seed)+fx*hashed(ix+1,iz+1,seed))*fz
def rock(x,y,z):
    # Large coherent dark/light patches, rather than block-by-block white speckle.
    n=noise(x*.24+y*.08,z*.24-y*.12,5)
    return 2 if n>.64 else 1

ground={}
# Rugged hill belongs to the left BACKGROUND. It rolls down in both directions.
for z in range(D):
    for x in range(W):
        low=3+int(noise(x*.10,z*.10,1)*2)
        hill=45*max(0,1-x/24)**1.25*math.exp(-((z-7)/30)**2)
        hill+=max(0,1-x/24)*6*(noise(x*.22,z*.17,2)-.5)
        if 4<z<39:
            hill-=max(0,1-abs(x-(7+2*math.sin(z*.20)))/2.5)*(4+5*noise(x*.2,z*.2,72))
        if 12<z<43:
            hill-=max(0,1-abs(x-(15+2*math.sin(z*.16)))/2)*5
        h=max(low,3+2*int(max(0,hill)/2))
        ground[x,z]=h
        for y in range(h+1):
            b=1 if y<h-3 else 2
            if y==h:
                threshold=.43 if h>10 else .28
                b=5 if noise(x*.32,z*.27,3)>threshold else rock(x,y,z)
                if h>9 and abs(x-(7+2*math.sin(z*.20)))<1.6: b=1
            put(x,y,z,b)
        # Cliff ledges occasionally project beyond a terrace line.
        if x<21 and h>10 and hashed(x,z,7)>.91:
            put(x,h+1,z,1 if hashed(x,z,8)>.4 else 5)

# A low irregular podium; visible retaining courses follow the sanctuary footprint.
for z in range(15,43):
    for x in range(18,48):
        if ((x-33)/16)**2+((z-29)/16)**2<1.12:
            box(x,0,z,x,7,z,2)
            put(x,7,z,5 if noise(x*.3,z*.3,10)>.62 else rock(x,7,z))
for z in (16,40):
    for x in range(23,44):
        if get(x,7,z): put(x,7,z,1)

# Broad flared stair: five 2-block-deep full-block treads.
for z in range(41,51):
    top=max(3,7-(z-41)//2)
    half=9+(z-41)//4
    for x in range(33-half,34+half):
        if abs(x-33)>half-2 and hashed(x,z,11)>.76: continue
        box(x,0,z,x,top,z,2)
        put(x,top,z,1 if z%2==0 or abs(x-33)>half-2 else 2)

def path(points,width=2):
    for a,b in zip(points,points[1:]):
        n=max(abs(a[i]-b[i]) for i in (0,1))*3
        for j in range(n+1):
            x=round(a[0]+(b[0]-a[0])*j/max(1,n)); z=round(a[1]+(b[1]-a[1])*j/max(1,n))
            for dx in range(-width,width+1):
                for dz in range(-width,width+1):
                    if dx*dx+dz*dz>(width+.4)**2: continue
                    xx,zz=x+dx,z+dz
                    if not (0<=xx<W and 0<=zz<D): continue
                    y=ground[xx,zz]
                    if y>9 or (18<=xx<=47 and 15<=zz<=41): continue
                    put(xx,y,zz,1 if max(abs(dx),abs(dz))==width and hashed(xx,zz,14)>.4 else 2)
path([(32,59),(34,54),(33,50)],3)
path([(26,57),(41,55),(52,48),(54,36),(52,23),(48,11)],2)
path([(12,53),(20,49),(25,47)],2)

def pier(cx,cz,base,top,rx=2,rz=2,broken=False):
    for y in range(base,top+1):
        foot=y<=base+2
        band=y in (base+3,base+13,top-2,top-1)
        ax=rx+1 if foot or band else rx
        az=rz+1 if foot or band else rz
        for z in range(cz-az,cz+az+1):
            for x in range(cx-ax,cx+ax+1):
                if abs(x-cx)==ax and abs(z-cz)==az: continue
                cap=top-int(hashed(x,z,20)*5) if broken else top
                if y>cap: continue
                put(x,y,z,rock(x,y,z))
    if broken:
        box(cx-1,top,cz-1,cx,top+2,cz,rock)
    # Restrained bright chips, only on a handful of fractured edges.
    if top-base>20:
        for y in (base+4,base+5,top-4): put(cx-rx,y,cz+rz,3)

def arch_x(cx,cz,span,spring,rise,inner_span,inner_rise,depth=5,broken_side=False):
    # Solid spandrels surrounding a carved rounded opening.
    for x in range(cx-span,cx+span+1):
        u=x-cx; t=abs(u)/span
        outer=spring+round(rise*math.sqrt(max(0,1-t*t)))
        ceiling=spring+round(inner_rise*math.sqrt(max(0,1-(u/inner_span)**2))) if abs(u)<=inner_span else spring-3
        for y in range(spring-3,outer+1):
            if abs(u)<=inner_span and y<=ceiling: continue
            for z in range(cz-depth//2,cz+depth//2+1):
                if broken_side and u>span-3 and y>outer-2: continue
                put(x,y,z,rock(x,y,z))

def arch_z(cx,cz,span,spring,rise,inner_span,inner_rise,depth=5,broken=False):
    for z in range(cz-span,cz+span+1):
        u=z-cz; outer=spring+round(rise*math.sqrt(max(0,1-(u/span)**2)))
        ceiling=spring+round(inner_rise*math.sqrt(max(0,1-(u/inner_span)**2))) if abs(u)<=inner_span else spring-3
        for y in range(spring-3,outer+1):
            if abs(u)<=inner_span and y<=ceiling: continue
            if broken and z>cz+1 and y>spring+rise-5: continue
            for x in range(cx-depth//2,cx+depth//2+1): put(x,y,z,rock(x,y,z))

# Heavy lower sanctuary. Front opening is framed by thick, articulated piers.
for x,z,top in [(23,36,31),(43,36,31),(23,20,39),(43,20,38)]:
    pier(x,z,8,top,2,2)
    # Buttresses split the mass into vertical ribs without decorative extra blocks.
    box(x-1,10,z+3,x+1,24,z+4,rock)
    box(x-1,25,z+3,x+1,27,z+3,rock)
arch_x(33,36,12,30,13,7,7,5)
arch_x(33,20,12,37,12,7,7,5,True)
arch_z(23,28,8,31,12,4,6,5)
arch_z(43,28,8,30,11,4,5,5,True)
# Horizontal projecting shoulders over the piers carry the moss blanket.
for x in (23,43):
    box(x-4,29,33,x+4,30,39,rock)
    box(x-3,31,33,x+3,32,39,rock)

# Broken upper rear arcade: smaller windows, continuous foot, irregular skyline.
skyline=[54,56,58,58,57,55,53,54,57,60,61,60,57,56,58,60,59,56,54,53,55,54,52,51,50]
for x in range(21,46):
    top=skyline[x-21]
    for y in range(39,top+1):
        # Upper window wall grows from a broad lintel, rather than a second giant ring.
        if x in (25,26,27,31,32,33,37,38,39,43) and 45<=y<=top-2: continue
        for z in range(18,22):
            # One diagonal bite cuts away the entire upper-right corner.
            if x>39 and y>54-(x-39)*2: continue
            put(x,y,z,rock(x,y,z))
# An attached, shattered left return wall suggests a second storey in depth.
for z in range(22,31):
    top=54-(z-22)//2
    for y in range(41,top):
        if z in (24,25,28) and y>45: continue
        for x in range(21,24): put(x,y,z,rock(x,y,z))
# An offset surviving inner pier interrupts the rear opening and carries the arcade.
pier(38,22,8,49,1,1)

# Freestanding ruins: uneven heights, rotations implied by off-centre fragments.
for x,z,top,rx in [(14,36,32,1),(19,46,18,1),(49,30,38,1),(51,19,42,1),(47,43,29,1),(36,13,27,1)]:
    pier(x,z,ground[x,z]+1,top,rx,1,True)
    if top>30:
        box(x-2,top-4,z,x+1,top-3,z+1,rock)
        box(x,top+1,z,x+1,top+2,z,rock)

# Fallen masonry is grouped into a few slabs, leaving the principal view open.
for cx,cz,n in [(19,40,9),(45,41,8),(46,21,7),(23,45,6),(38,14,5),(16,31,5)]:
    for _ in range(n):
        x=cx+rng.randrange(-3,4); z=cz+rng.randrange(-3,4)
        if 28<=x<=38 and z>32: continue
        y=max((yy for yy in range(15) if get(x,yy,z)),default=3)+1
        if y>11: continue
        box(x,y,z,x+rng.randrange(1,3),y+rng.randrange(0,2),z+rng.randrange(1,3),rock)

# Heavy moss grows in connected patches over arch shoulders and broken cornices.
for y in range(12,63):
    for z in range(15,41):
        for x in range(18,48):
            if get(x,y,z) in (1,2) and get(x,y+1,z)==0:
                lush=noise(x*.28,z*.27,30)+.18*math.sin(y*.3)
                if lush>.49:
                    put(x,y,z,5)
                    if y>29 and noise(x*.38,z*.37,31)>.6: put(x,y+1,z,5)
# Dense, asymmetric overgrowth masks the arch crown, as in the reference.
for x in range(24,43):
    for z in range(32,40):
        tops=[y for y in range(30,47) if get(x,y,z)]
        if not tops or noise(x*.25,z*.27,32)<.32: continue
        y=max(tops)
        put(x,y,z,5)
        if noise(x*.37,z*.4,33)>.47: put(x,y+1,z,5)
for cx,cy,cz,rx,ry,rz in [(28,42,36,4,3,4),(39,39,36,4,3,3),(24,35,35,3,3,3)]:
    for y in range(cy-ry,cy+ry+1):
        for z in range(cz-rz,cz+rz+1):
            for x in range(cx-rx,cx+rx+1):
                d=((x-cx)/rx)**2+((y-cy)/ry)**2+((z-cz)/rz)**2
                if d<.9+.25*noise(x*.4,z*.4+y*.2,75): put(x,y,z,5)
for x,z,end in [(29,39,29),(30,39,31),(31,39,33),(36,39,34),(37,39,32)]:
    tops=[y for y in range(33,46) if get(x,y,z)==5]
    if tops:
        for y in range(end,max(tops)+1): put(x,y,z,5)
for x,z,length in [(25,39,9),(26,39,7),(27,39,5),(29,38,5),(38,39,8),(39,39,10),(40,39,6),(23,31,8),(21,28,6),(42,24,7)]:
    tops=[y for y in range(30,48) if get(x,y,z)]
    if not tops:
        # Root each pendant into nearby masonry rather than floating in space.
        roots=[(abs(xx-x)+abs(zz-z),xx,yy,zz) for xx in range(x-1,x+2) for zz in range(z-1,z+2) for yy in range(34,45) if get(xx,yy,zz)]
        if not roots: continue
        _,xx,y,zz=min(roots); put(x,y,z,5)
    else: y=max(tops)
    for yy in range(max(24,y-length),y+1):
        put(x,yy,z,5)
        if yy>y-length+2 and hashed(yy,x+z,34)>.48: put(x+1,yy,z,5)

def line(a,b,mat=4):
    n=max(abs(b[i]-a[i]) for i in range(3))
    for j in range(n+1):
        p=tuple(round(a[i]+(b[i]-a[i])*j/max(1,n)) for i in range(3)); put(*p,mat)
def crown(cx,cy,cz,rad):
    # Entire crown is warped hyphae, NOT leaves; irregular overlapping layers.
    for dy in range(-1,3):
        radius=max(1,rad-(1 if dy==2 else 0))
        for dz in range(-radius,radius+1):
            for dx in range(-radius,radius+1):
                if dx*dx+dz*dz>(radius+.2)**2: continue
                if abs(dx)+abs(dz)>radius and hashed(cx+dx,cz+dz,cy+dy)>.88: continue
                x,y,z=cx+dx,cy+dy,cz+dz
                if get(x,y,z)==0: put(x,y,z,4)
def tree(x,z,height,rad=3):
    base=ground[x,z]+1
    if base>22: return
    lean=1 if hashed(x,z,41)>.5 else -1
    line((x,base,z),(x+lean,base+height,z))
    if height>14: line((x+1,base,z),(x+lean+1,base+height-4,z))
    for k in range(3):
        a=k*2.4+hashed(x,z,k)*1.1
        reach=rad+1
        bx=x+round(math.cos(a)*reach); bz=z+round(math.sin(a)*reach)
        by=base+height-3-k*2
        line((x+lean,by-3,z),(bx,by,bz))
        crown(bx,by,bz,rad)
    crown(x+lean,base+height,z,rad)

# Overlapping low canopy surrounds the shrine; no foreground tree hides the entry.
trees=[(53,8,14,3),(46,7,16,3),(38,6,12,3),(30,7,13,3),
       (57,15,13,3),(56,25,15,3),(56,34,12,3),(55,42,15,3),
       (53,50,12,3),(47,52,13,3),(44,57,10,2),(53,57,11,3),
       (16,54,12,3),(11,47,13,3),(10,39,13,3),(17,27,11,2),
       (18,18,12,2),(24,12,12,2),(48,15,10,2),(48,37,9,2),
       (42,10,10,2),(58,52,12,2),(9,57,11,2),(4,51,10,2)]
for x,z,height,rad in trees: tree(x,z,height,rad)
# Low warped-wood undergrowth ties the isolated trunks into a continuous forest.
for _ in range(200):
    x=rng.randrange(3,58); z=rng.randrange(4,58)
    if 18<=x<=47 and 14<=z<=51: continue
    if z>49 and 20<x<43: continue
    if x<19 and ground[x,z]>18: continue
    if not any((x-tx)**2+(z-tz)**2<40 for tx,tz,_,_ in trees): continue
    y=ground[x,z]+1
    if get(x,y,z)==0 and hashed(x,z,60)>.4:
        for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]:
            if get(x+dx,y,z+dz)==0: put(x+dx,y,z+dz,4)
        if hashed(x,z,61)>.5: put(x,y+1,z,4)

# Final pedestrian corridor: five-wide, with a four-block clear envelope.
route=[]
for z in range(14,59):
    floor=7 if z<=42 else max(3,7-(z-41)//2)
    for x in range(31,36):
        box(x,0,z,x,floor,z,2)
        box(x,floor+1,z,x,floor+4,z,0)
        put(x,floor,z,2 if noise(x*.3,z*.3,70)>.3 else 1)
    route.append((33,floor+1,z))


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
meta={'Name':(8,'Overgrown Sanctuary - Reference Rebuild'),'Author':(8,'OpenAI'),
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
       'Metadata':(10,{'Name':(8,'Overgrown Sanctuary - Reference Rebuild')})}
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
report={'dimensions':{'x':W,'y':H,'z':D},'minecraft_data_version':DATA_VERSION,'layout_revision':2,'highest_occupied_y':max(i//(W*D) for i,b in enumerate(blocks) if b),
        'non_air_blocks':count,'palette_counts':{p:counts[i] for i,p in enumerate(PALETTE)},
        'validation':{'gzip_nbt_roundtrip':True,'litematica_all_packed_states_match':True,
                      'worldedit_all_blocks_match':True,'entrance_route_width':5,
                      'entrance_route_clearance':4,'entrance_route_length':len(route),
                      'max_route_step':1,'in_game_tested':False},
        'orientation':'Front is +Z; left slope is -X. Region minimum corner is (0,0,0).'}
Path('validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
