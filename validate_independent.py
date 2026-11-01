#!/usr/bin/env python3
"""Read-only, independent schematic audit. Python standard library only."""
import gzip, struct, json, hashlib
from pathlib import Path
from collections import Counter

class NBT:
    def __init__(self, path): self.data=gzip.decompress(Path(path).read_bytes()); self.i=0
    def take(self,n):
        if n<0 or self.i+n>len(self.data): raise ValueError('Invalid NBT length')
        v=self.data[self.i:self.i+n]; self.i+=n; return v
    def number(self,f): return struct.unpack('>'+f,self.take(struct.calcsize('>'+f)))[0]
    def string(self): return self.take(self.number('H')).decode('utf-8')
    def read(self,t):
        if t in {1,2,3,4,5,6}: return self.number({1:'b',2:'h',3:'i',4:'q',5:'f',6:'d'}[t])
        if t==8: return self.string()
        if t==7: return self.take(self.number('i'))
        if t in (11,12):
            n=self.number('i'); assert n>=0
            return [self.number('i' if t==11 else 'q') for _ in range(n)]
        if t==9:
            item=self.number('B'); n=self.number('i'); assert n>=0
            return [self.read(item) for _ in range(n)]
        if t==10:
            d={}
            while True:
                child=self.number('B')
                if not child: return d
                k=self.string(); assert k not in d
                d[k]=self.read(child)
        raise ValueError('Unknown tag '+str(t))
    def root(self):
        assert self.number('B')==10
        name=self.string(); body=self.read(10); assert self.i==len(self.data)
        return name,body

ALLOWED={'minecraft:air','minecraft:smooth_basalt','minecraft:stone','minecraft:calcite','minecraft:warped_hyphae','minecraft:moss_block'}

def audit(directory,stem,w,h,d,xc,width,zlo,zhi,flat,formula):
    directory=Path(directory)
    lp=directory/(stem+'.litematic'); sp=directory/(stem+'.schem')
    lname,l=NBT(lp).root(); sname,s=NBT(sp).root()
    assert l['Version']==6 and l['SubVersion']==1
    assert l['MinecraftDataVersion']==s['DataVersion']==4671
    assert len(l['Regions'])==1 and l['Metadata']['RegionCount']==1
    r=next(iter(l['Regions'].values()))
    assert r['Position']==dict(x=0,y=0,z=0)
    assert r['Size']==l['Metadata']['EnclosingSize']==dict(x=w,y=h,z=d)
    palette=[a['Name'] for a in r['BlockStatePalette']]
    assert len(palette)==6 and set(palette)==ALLOWED and palette[0]=='minecraft:air'
    bitwidth=max(2,(len(palette)-1).bit_length()); volume=w*h*d
    longs=[a&((1<<64)-1) for a in r['BlockStates']]
    assert len(longs)==(volume*bitwidth+63)//64
    vox=bytearray(volume)
    for i in range(volume):
        b=i*bitwidth; word,shift=divmod(b,64)
        value=longs[word]>>shift
        if shift+bitwidth>64: value |= longs[word+1]<<(64-shift)
        v=value&((1<<bitwidth)-1); assert v<len(palette); vox[i]=v
    assert sname=='Schematic' and s['Version']==2
    assert (s['Width'],s['Height'],s['Length'])==(w,h,d)
    assert s['Offset']==[0,0,0] and s['PaletteMax']==6
    assert s['Palette']=={p:i for i,p in enumerate(palette)}
    data=s['BlockData']; si=0; unfolded=bytearray()
    while si<len(data):
        v=0; shift=0
        while True:
            q=data[si];si+=1;v|=(q&127)<<shift;shift+=7
            assert shift<=35
            if not q&128:break
        assert v<6;unfolded.append(v)
    assert unfolded==vox and len(unfolded)==volume
    counts=Counter(vox);nonair=volume-counts[0]
    assert l['Metadata']['TotalBlocks']==nonair and l['Metadata']['TotalVolume']==volume
    assert not r['Entities'] and not r['TileEntities'] and not s['BlockEntities'] and not s['Entities']
    def at(x,y,z): return vox[(y*d+z)*w+x]
    route=[]
    for z in range(zlo,zhi+1):
        floor=flat if z<=formula[0] else max(3,flat-(z-formula[0])//formula[1])
        for x in range(xc-width//2,xc+width//2+1):
            assert at(x,floor,z)!=0,(x,floor,z,'missing floor')
            assert all(at(x,y,z)==0 for y in range(floor+1,floor+5)),(x,floor,z,'blocked headroom')
        route.append((xc,floor+1,z))
    assert all(abs(a[1]-b[1])<=1 for a,b in zip(route,route[1:]))
    # Ensure adjacent steps can be traversed with 2-block player headroom at both sides.
    for a,b in zip(route,route[1:]):
        high=max(a[1],b[1])
        for p in (a,b):
            assert at(p[0],high,p[2])==at(p[0],high+1,p[2])==0
    highest=max(i//(w*d) for i,b in enumerate(vox) if b)
    return {'size':[w,h,d],'non_air_blocks':nonair,'counts':{p:counts[i] for i,p in enumerate(palette)},
            'highest_occupied_y':highest,'clear_route_width':width,'clear_route_height':4,
            'clear_route_length':len(route),'all_checks_passed':True,'in_game_tested':False,
            'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (lp,sp)}}

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    report={
        'large':audit(root/'original','overgrown_sanctuary',129,88,129,67,7,18,111,9,(84,3)),
        'compact':audit(root/'compact','overgrown_sanctuary_60x88x60',60,88,60,31,5,8,54,9,(39,2)),
        'checks':['gzip CRC and NBT complete parsing','Litematica v6 header and required tags','independent packed-state decoding','Sponge v2 header and VarInt block decoding','all blocks identical across formats','strict six-entry palette','metadata counts','full corridor width and 4-block headroom','single-block stairs and adjacent-step player headroom'],
        'data_version_note':'Both files declare 4671 (Java 1.21.11). No running Minecraft client available.'}
    (root/'audit_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
