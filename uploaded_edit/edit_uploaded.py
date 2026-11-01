#!/usr/bin/env python3
"""Height-preserving edit; all basalt replaced with cobblestone/mossy cobblestone. Standard library only."""
import argparse,collections,gzip,hashlib,json,math,struct
from pathlib import Path

class NBT:
    def __init__(self,path): self.data=gzip.decompress(Path(path).read_bytes()); self.i=0
    def take(self,n):
        if n<0 or self.i+n>len(self.data): raise ValueError('Invalid NBT length')
        b=self.data[self.i:self.i+n]; self.i+=n; return b
    def number(self,f): return struct.unpack('>'+f,self.take(struct.calcsize('>'+f)))[0]
    def string(self): return self.take(self.number('H')).decode('utf8')
    def read(self,t):
        if t in (1,2,3,4,5,6): return self.number({1:'b',2:'h',3:'i',4:'q',5:'f',6:'d'}[t])
        if t==8: return self.string()
        if t==7: return self.take(self.number('i'))
        if t in (11,12):
            n=self.number('i'); assert n>=0
            return [self.number('i' if t==11 else 'q') for _ in range(n)]
        if t==9:
            child=self.number('B'); n=self.number('i'); assert n>=0
            return [self.read(child) for _ in range(n)]
        if t==10:
            o={}
            while True:
                child=self.number('B')
                if child==0: return o
                k=self.string(); assert k not in o; o[k]=self.read(child)
        raise ValueError('Unknown tag '+str(t))
    def root(self):
        assert self.number('B')==10
        name=self.string(); body=self.read(10); assert self.i==len(self.data)
        return name,body

def text(v):
    b=v.encode('utf8'); return struct.pack('>H',len(b))+b
def payload(t,v):
    if t in (2,3,4): return struct.pack({2:'>h',3:'>i',4:'>q'}[t],v)
    if t==8: return text(v)
    if t==7: return struct.pack('>i',len(v))+bytes(v)
    if t==9:
        child,items=v; return bytes([child])+struct.pack('>i',len(items))+b''.join(payload(child,q) for q in items)
    if t==10: return b''.join(bytes([tt])+text(k)+payload(tt,value) for k,(tt,value) in v.items())+b'\0'
    if t in (11,12):
        return struct.pack('>i',len(v))+b''.join(struct.pack('>i' if t==11 else '>Q',q if t==11 else q&((1<<64)-1)) for q in v)
    raise ValueError(t)
def save(path,root,name=''):
    Path(path).write_bytes(gzip.compress(b'\x0a'+text(name)+payload(10,root),mtime=0))
def vec(x,y,z): return {k:(3,v) for k,v in zip(('x','y','z'),(x,y,z))}
def varints(data):
    result=[]; p=0
    while p<len(data):
        value=0; shift=0
        while True:
            q=data[p]; p+=1; value|=(q&127)<<shift; shift+=7
            assert shift<=35
            if q<128: break
        result.append(value)
    return result

def run(source,dest):
    _,s=NBT(source).root()
    assert s['Version']==2
    W,H,D=s['Width'],s['Height'],s['Length']
    assert (W,H,D)==(55,34,51),'This edit is designed specifically for the supplied original.'
    original=varints(s['BlockData']); assert len(original)==W*H*D
    palette=['minecraft:air','minecraft:stone','minecraft:moss_block',
             'minecraft:warped_hyphae[axis=y]','minecraft:calcite','minecraft:smooth_basalt',
             'minecraft:warped_hyphae[axis=x]']
    oldnames={v:k for k,v in s['Palette'].items()}
    def remap(name):
        if name=='minecraft:cobblestone': return 'minecraft:stone'
        return name.replace('minecraft:warped_stem','minecraft:warped_hyphae')
    lookup={v:palette.index(remap(k)) for k,v in s['Palette'].items()}
    blocks=bytearray(lookup[b] for b in original)
    base=blocks[:]
    def index(x,y,z): return (y*D+z)*W+x
    def get(x,y,z): return blocks[index(x,y,z)] if 0<=x<W and 0<=y<H and 0<=z<D else 0
    def put(x,y,z,b):
        assert 0<=x<W and 0<=y<H and 0<=z<D
        blocks[index(x,y,z)]=b
    def hashed(x,y,z): return ((x*73856093^y*19349663^z*83492791)&65535)/65535
    # Weather only existing exposed masonry. No pillar/arch blocks are moved or removed.
    patches=[(23,25,30,5,3,3),(34,22,30,4,3,3),(21,29,19,4,3,3),(18,17,24,2,4,3)]
    moss_changes=[]
    for cx,cy,cz,rx,ry,rz in patches:
        candidates=[]
        for y in range(max(6,cy-ry),min(H-1,cy+ry+1)):
            for z in range(cz-rz,cz+rz+1):
                for x in range(cx-rx,cx+rx+1):
                    if get(x,y,z) not in (1,5): continue
                    dd=((x-cx)/rx)**2+((y-cy)/ry)**2+((z-cz)/rz)**2
                    exposed=any(get(x+dx,y+dy,z+dz)==0 for dx,dy,dz in [(0,1,0),(1,0,0),(-1,0,0),(0,0,1),(0,0,-1)])
                    if exposed and dd<.9+hashed(x,y,z)*.18: candidates.append((dd,x,y,z))
        for _,x,y,z in sorted(candidates)[:24]:
            put(x,y,z,2); moss_changes.append([x,y,z])
    # Three small, supported debris groups, all outside the five-wide route.
    rubble=[]
    for cx,cz in [(20,34),(35,34),(16,25)]:
        candidates=[]
        for z in range(cz-2,cz+3):
            for x in range(cx-2,cx+3):
                if 24<=x<=30 and 14<=z<=50: continue
                top=max((y for y in range(6) if get(x,y,z)),default=-1)
                if top<0 or top>4 or get(x,top+1,z) or get(x,top,z) in (3,4,6): continue
                candidates.append(((x-cx)**2+(z-cz)**2,x,top+1,z))
        for n,(_,x,y,z) in enumerate(sorted(candidates)[:4]):
            put(x,y,z,1 if n%3 else 5); rubble.append([x,y,z])
    floor_repairs=[[28,0,43],[27,0,44],[25,0,49]]
    for x,y,z in floor_repairs:
        assert get(x,y,z)==0; put(x,y,z,1)

    # Material-only revision: retain one third of the previous edition's basalt.
    # The two newly requested block types intentionally extend the former palette.
    before_basalt_change=blocks[:]
    basalt_positions=[i for i,b in enumerate(blocks) if b==5]
    basalt_before=len(basalt_positions)
    keep_basalt=(basalt_before+1)//3
    cobble_id=len(palette); palette.append('minecraft:cobblestone')
    mossy_id=len(palette); palette.append('minecraft:mossy_cobblestone')
    def coords(i): return i%W,i//(W*D),(i//W)%D
    def basalt_field(i):
        x,y,z=coords(i)
        return .55*math.sin(x*.4+y*.21+z*.13)+.32*math.cos(z*.37-y*.29)+.12*hashed(x,y,z)
    # Broad irregular patches instead of a checkerboard or abrupt uniform layer.
    replacement=sorted(basalt_positions,key=lambda i:(basalt_field(i),i))[:basalt_before-keep_basalt]
    def moss_field(i):
        x,y,z=coords(i)
        near_moss=sum(get(x+dx,y+dy,z+dz)==2 for dx,dy,dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)])
        return .6*near_moss+.5*math.cos(x*.35-z*.2)+.3*math.sin(y*.55+z*.31)-.01*y+.1*hashed(x,y,z)
    mossy_count=len(replacement)//2
    mossy_positions=set(sorted(replacement,key=lambda i:(moss_field(i),i),reverse=True)[:mossy_count])
    for i in replacement: blocks[i]=mossy_id if i in mossy_positions else cobble_id
    assert sum(b==5 for b in blocks)==keep_basalt
    assert all(a==b or a==5 and b in (cobble_id,mossy_id) for a,b in zip(before_basalt_change,blocks))
    assert all(bool(a)==bool(b) for a,b in zip(before_basalt_change,blocks))

    # Latest request: replace only the remaining basalt; keep the preceding mix exact.
    preceding_edition=blocks[:]
    remaining_positions=[i for i,b in enumerate(blocks) if b==5]
    more_mossy=(len(remaining_positions)+1)//2
    last_mossy=set(sorted(remaining_positions,key=lambda i:(moss_field(i),i),reverse=True)[:more_mossy])
    for i in remaining_positions: blocks[i]=mossy_id if i in last_mossy else cobble_id
    assert all(a==b or a==5 and b in (cobble_id,mossy_id) for a,b in zip(preceding_edition,blocks))
    assert 5 not in blocks
    replacement+=remaining_positions
    mossy_count+=more_mossy
    keep_basalt=0

    # Preserve the entire existing occupied geometry and both original topmost blocks.
    assert all(not old or new for old,new in zip(original,blocks))
    assert get(25,33,18)==get(30,33,18)==2
    assert all(not blocks[i] or original[i] for i in range(33*W*D,len(blocks)))
    def bounds(data):
        points=[(i%W,i//(W*D),(i//W)%D) for i,b in enumerate(data) if b]
        return [[min(p[j] for p in points),max(p[j] for p in points)] for j in range(3)]
    assert bounds(original)==bounds(blocks)
    route=[]
    for z in range(15,51):
        floor=0 if z>=40 else 1 if z>=38 else 2 if z==37 else 3 if z>=34 else 4
        for x in range(25,30):
            assert get(x,floor,z)!=0
            assert get(x,floor+1,z)==get(x,floor+2,z)==0
        route.append((27,floor+1,z))
    for a,b in zip(route,route[1:]):
        assert abs(a[1]-b[1])<=1
        high=max(a[1],b[1])
        for x,_,z in (a,b): assert get(x,high,z)==get(x,high+1,z)==0

    # Remove basalt from the exported palette too (nine states become eight).
    old_palette=palette
    used=sorted(set(blocks))
    state_remap={old:new for new,old in enumerate(used)}
    palette=[old_palette[i] for i in used]
    blocks=bytearray(state_remap[b] for b in blocks)
    assert all('basalt' not in state for state in palette)

    dest=Path(dest); dest.mkdir(parents=True,exist_ok=True)
    stem='ancient_ruins_warped_edited'
    nonair=sum(bool(b) for b in blocks)
    schem={'Version':(3,2),'DataVersion':(3,4671),'Width':(2,W),'Height':(2,H),'Length':(2,D),
           'Offset':(11,s['Offset']),'PaletteMax':(3,len(palette)),
           'Palette':(10,{name:(3,i) for i,name in enumerate(palette)}),
           'BlockData':(7,blocks),'BlockEntities':(9,(10,[])),'Entities':(9,(10,[])),
           'Metadata':(10,{'Name':(8,'Ancient Ruins - No Basalt, original height')})}
    save(dest/(stem+'.schem'),schem,'Schematic')
    bits=max(2,(len(palette)-1).bit_length()); states=[0]*math.ceil(len(blocks)*bits/64)
    for i,b in enumerate(blocks):
        q,shift=divmod(i*bits,64); states[q]|=(b<<shift)&((1<<64)-1)
        if shift+bits>64: states[q+1]|=b>>(64-shift)
    state_palette=[]
    for state in palette:
        name=state.split('[')[0]; entry={'Name':(8,name)}
        if '[' in state:
            properties=dict(p.split('=') for p in state.split('[')[1][:-1].split(','))
            entry['Properties']=(10,{k:(8,v) for k,v in properties.items()})
        state_palette.append(entry)
    region={'Position':(10,vec(0,0,0)),'Size':(10,vec(W,H,D)),
            'BlockStatePalette':(9,(10,state_palette)),'BlockStates':(12,states),
            'Entities':(9,(10,[])),'TileEntities':(9,(10,[])),
            'PendingBlockTicks':(9,(10,[])),'PendingFluidTicks':(9,(10,[]))}
    meta={'Name':(8,'Ancient Ruins - No Basalt'),'Author':(8,'Uploaded build; local edits'),
          'Description':(8,'Original height preserved; all basalt replaced with cobblestone and mossy cobblestone.'),
          'RegionCount':(3,1),'TimeCreated':(4,1793577600000),'TimeModified':(4,1793577600000),
          'TotalBlocks':(3,nonair),'TotalVolume':(3,len(blocks)),'EnclosingSize':(10,vec(W,H,D))}
    save(dest/(stem+'.litematic'),{'Version':(3,6),'SubVersion':(3,1),'MinecraftDataVersion':(3,4671),
         'Metadata':(10,meta),'Regions':(10,{'Ruins':(10,region)})})
    _,r=NBT(dest/(stem+'.litematic')).root(); rr=r['Regions']['Ruins']
    decoded=[]; longs=[q&((1<<64)-1) for q in rr['BlockStates']]
    for i in range(len(blocks)):
        q,shift=divmod(i*bits,64); v=longs[q]>>shift
        if shift+bits>64: v|=longs[q+1]<<(64-shift)
        decoded.append(v&((1<<bits)-1))
    assert decoded==list(blocks)
    _,r=NBT(dest/(stem+'.schem')).root(); assert varints(r['BlockData'])==list(blocks)
    counts=collections.Counter(blocks)
    report={'dimensions_xyz':[W,H,D],'source_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),
            'minecraft_data_version':4671,'source_non_air_blocks':sum(bool(q) for q in original),'non_air_blocks':nonair,
            'source_bounds_xyz':bounds(original),'edited_bounds_xyz':bounds(blocks),
            'palette_counts':{name:counts[i] for i,name in enumerate(palette)},
            'changes':{'cobblestone_to_stone':sum(oldnames[q]=='minecraft:cobblestone' for q in original),
                       'warped_stem_to_hyphae':sum(oldnames[q].startswith('minecraft:warped_stem') for q in original),
                       'new_moss_on_existing_masonry':moss_changes,'added_rubble':rubble,'floor_holes_repaired':floor_repairs,
                       'basalt_replacement':{'baseline_basalt':basalt_before,'remaining_basalt':keep_basalt,
                                            'added_cobblestone':len(replacement)-mossy_count,'added_mossy_cobblestone':mossy_count,
                                            'replaced_in_latest_revision':len(remaining_positions),
                                            'latest_added_cobblestone':len(remaining_positions)-more_mossy,'latest_added_mossy_cobblestone':more_mossy,
                                            'basalt_absent_from_palette':True,
                                            'geometry_unchanged_from_previous_edit':True,'other_block_states_unchanged':True}},
            'validation':{'same_selection_dimensions':True,'same_occupied_bounds':True,'same_topmost_blocks':True,
                          'all_original_occupied_positions_retained':True,'blocks_removed_or_moved':0,
                          'full_block_roundtrip_both_formats':True,'route_width':5,'route_clearance':2,'route_length':36,
                          'maximum_route_step':1,'in_game_tested':False},
            'sha256':{ext:hashlib.sha256((dest/(stem+ext)).read_bytes()).hexdigest() for ext in ('.schem','.litematic')}}
    (dest/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('changes','palette_counts')},indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path(__file__).with_name('ancient_ruins_warped.schem'))
    parser.add_argument('--output',type=Path,default=Path(__file__).parent)
    args=parser.parse_args(); run(args.input,args.output)
