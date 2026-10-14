# Writes favicon.ico + favicon.png in the site palette: python3 _build/favicon.py .
import zlib,struct,sys,os
out=sys.argv[1]
BG=(0x17,0x23,0x3C);FG=(0xC2,0x42,0x2B)
def render(n,ss=4):
    rows=[]
    for y in range(n):
        row=bytearray()
        for x in range(n):
            acc=[0,0,0,0]
            for sy in range(ss):
                for sx in range(ss):
                    u=(x+(sx+.5)/ss)/n; v=(y+(sy+.5)/ss)/n
                    # rounded square, radius 0.18
                    r=.18; dx=max(abs(u-.5)-(.5-r),0); dy=max(abs(v-.5)-(.5-r),0)
                    if dx*dx+dy*dy>r*r: continue
                    c=FG if (u-.5)**2+(v-.5)**2<=.29**2 else BG
                    acc[0]+=c[0];acc[1]+=c[1];acc[2]+=c[2];acc[3]+=1
            k=acc[3]
            row+=bytes([acc[0]//k,acc[1]//k,acc[2]//k,255*k//(ss*ss)] if k else [0,0,0,0])
        rows.append(row)
    return rows
def png(n):
    raw=b"".join(b"\0"+bytes(r) for r in render(n))
    ch=lambda t,d:struct.pack(">I",len(d))+t+d+struct.pack(">I",zlib.crc32(t+d)&0xffffffff)
    return b"\x89PNG\r\n\x1a\n"+ch(b"IHDR",struct.pack(">IIBBBBB",n,n,8,6,0,0,0))+ch(b"IDAT",zlib.compress(raw,9))+ch(b"IEND",b"")
sizes=[16,32,48]; imgs=[png(s) for s in sizes]
hdr=struct.pack("<HHH",0,1,len(sizes)); off=6+16*len(sizes); ent=b""
for s,d in zip(sizes,imgs):
    ent+=struct.pack("<BBBBHHII",s,s,0,0,1,32,len(d),off); off+=len(d)
open(os.path.join(out,"favicon.ico"),"wb").write(hdr+ent+b"".join(imgs))
open(os.path.join(out,"favicon.png"),"wb").write(png(180))
