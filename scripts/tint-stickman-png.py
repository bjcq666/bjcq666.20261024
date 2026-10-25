"""RGBA8 PNG tint/mirror utility; preserves alpha and canvas size."""
import struct,zlib,binascii
COLOR=(255,2,99)

def transform(blob,mirror=False):
    pos=8;compressed=b''
    while pos<len(blob):
        n=struct.unpack('>I',blob[pos:pos+4])[0];typ=blob[pos+4:pos+8];d=blob[pos+8:pos+8+n];pos+=n+12
        if typ==b'IHDR':header=d;w,h,depth,color,_,_,inter=struct.unpack('>IIBBBBB',d)
        if typ==b'IDAT':compressed+=d
    assert (depth,color,inter)==(8,6,0)
    raw=zlib.decompress(compressed);stride=w*4;prev=bytearray(stride);offset=0;output=bytearray()
    for y in range(h):
        filt=raw[offset];offset+=1;row=bytearray(raw[offset:offset+stride]);offset+=stride
        for x in range(stride):
            a=row[x-4] if x>=4 else 0;b=prev[x];c=prev[x-4] if x>=4 else 0
            if filt==0:pred=0
            elif filt==1:pred=a
            elif filt==2:pred=b
            elif filt==3:pred=(a+b)//2
            elif filt==4:
                p=a+b-c;pa,pb,pc=abs(p-a),abs(p-b),abs(p-c);pred=a if pa<=pb and pa<=pc else (b if pb<=pc else c)
            else:raise ValueError('Unsupported PNG filter')
            row[x]=(row[x]+pred)&255
        prev=row
        output.append(0)
        for x in range(w):
            source_x=w-1-x if mirror else x
            output.extend((*COLOR,row[source_x*4+3]))
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',binascii.crc32(t+d)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+chunk(b'IDAT',zlib.compress(output,9))+chunk(b'IEND',b'')
