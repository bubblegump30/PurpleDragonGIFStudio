"""Looping turbulent fire, volumetric glow and embers; no polygon tongues."""
import math
from functools import lru_cache
import numpy as np
from PIL import Image,ImageFilter

COLORS=['Orange','Crimson','Gold','Blue','Cyan','Purple','Green','Rainbow']
STYLES=['Campfire','Inferno','Torch jets','Wispy fire','Ember storm','Smoke and fire']

@lru_cache(maxsize=12)
def lattice(seed):
    return np.random.default_rng(seed).random((16,16),dtype=np.float32)

def noise(x,y,seed):
    grid=lattice(seed);ix=np.floor(x).astype(np.int32);iy=np.floor(y).astype(np.int32)
    fx=x-ix;fy=y-iy;fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy)
    a=grid[iy%16,ix%16]*(1-fx)+grid[iy%16,(ix+1)%16]*fx
    b=grid[(iy+1)%16,ix%16]*(1-fx)+grid[(iy+1)%16,(ix+1)%16]*fx
    return a*(1-fy)+b*fy

def spectrum(heat,color,phase):
    ramps={
      'Orange':[(80,3,0),(225,30,1),(255,115,5),(255,210,70),(255,250,218)],
      'Crimson':[(50,0,8),(175,2,15),(250,25,35),(255,112,76),(255,227,195)],
      'Gold':[(70,20,0),(194,85,0),(255,166,6),(255,222,85),(255,253,221)],
      'Blue':[(0,4,65),(8,40,180),(10,125,255),(85,211,255),(218,249,255)],
      'Cyan':[(0,26,36),(0,104,137),(4,219,231),(85,255,243),(223,255,248)],
      'Purple':[(31,0,57),(93,5,165),(170,33,255),(232,128,255),(255,235,255)],
      'Green':[(1,24,2),(11,98,5),(45,209,15),(177,250,55),(243,255,211)]}
    if color=='Rainbow':
        from colorsys import hsv_to_rgb
        hue=(phase/(2*math.pi)+.12)%1
        base=np.array(hsv_to_rgb(hue,1,1))*255
        ramp=np.array([base*.15,base*.55,base,base*.65+255*.35,base*.1+255*.9],dtype=np.float32)
    else:ramp=np.array(ramps.get(color,ramps['Orange']),dtype=np.float32)
    positions=np.linspace(0,1,len(ramp))
    return np.stack([np.interp(heat,positions,ramp[:,c]) for c in range(3)],axis=-1)

def fire_layer(size,phase,strength,color,style):
    w,h=size;x,y=np.meshgrid(np.linspace(0,1,w,dtype=np.float32),np.linspace(1,0,h,dtype=np.float32))
    t=phase/(2*math.pi)
    drift=.15*np.sin(phase+x*9)+.065*np.sin(phase*2+y*8)
    n1=noise(x*7+drift,y*5+t*16,21)
    n2=noise(x*17+n1*.8,y*12+t*16,37)
    n3=noise(x*41+n2*.5,y*25+t*16,93)
    n4=noise(x*89+n3,y*62+t*16,119)
    turbulence=.51*n1+.27*n2+.16*n3+.06*n4
    plume=.48+.52*noise(x*7+np.sin(phase)*.3,t*16+np.zeros_like(x),55)
    height=.17+.46*strength
    if style=='Inferno':height*=1.55;plume=.7+.45*plume
    elif style=='Torch jets':
        jets=np.maximum.reduce([np.exp(-((x-c-.025*np.sin(phase+y*7))/.05)**2) for c in [.18,.5,.82]])
        plume*=jets; height*=1.4
    elif style=='Wispy fire':height*=1.6;plume*=.8
    elif style=='Ember storm':height*=.85
    envelope=height*plume
    pressure=envelope-y+(turbulence-.5)*height*.85
    alpha=np.clip(pressure/(.035+height*.06)+.5,0,1)
    alpha*=np.clip(1-y/(height*1.8),0,1)
    if style=='Wispy fire':alpha*=.7+.3*n3
    heat=np.clip((1-y/np.maximum(envelope,.025))*.7+turbulence*.43+n3*.10+n4*.06,0,1)
    rgb=spectrum(heat,color,phase)
    image=Image.fromarray(np.dstack((rgb,np.clip(alpha*230,0,255))).astype(np.uint8),'RGBA')
    # Layer smoke behind fire rather than drawing opaque grey polygons.
    if style=='Smoke and fire':
        smoke_alpha=np.clip((height*1.8-y)/(height*1.6),0,1)*np.clip((turbulence-.35)*1.6,0,1)*np.clip(y/height,0,1)*70
        smoke=Image.fromarray(np.dstack((np.full_like(x,74),np.full_like(x,69),np.full_like(x,79),smoke_alpha)).astype(np.uint8),'RGBA').filter(ImageFilter.GaussianBlur(max(1,w/180)))
        smoke.alpha_composite(image);image=smoke
    glow=image.filter(ImageFilter.GaussianBlur(max(2,w/85)))
    glow.alpha_composite(image)
    from PIL import ImageDraw
    sparks=Image.new('RGBA',size);draw=ImageDraw.Draw(sparks)
    rng=np.random.default_rng(173)
    for i in range(85 if style=='Ember storm' else 20):
        sx,offset,speed=rng.random(3)
        life=(t*(1+int(speed*3))+offset)%1
        px=(sx+.025*math.sin(phase+life*7+i))*w
        py=h*(1-life*(.9 if style=='Ember storm' else .65))
        radius=max(.5,w/600)*(1-life*.7)
        tint=tuple(int(v) for v in spectrum(np.array(.6),color,phase))+ (int(220*(1-life)),)
        draw.ellipse((px-radius,py-radius,px+radius,py+radius),fill=tint)
    glow.alpha_composite(sparks)
    return glow

def overlay(frame,phase,intensity=55,color='Orange',placement='Bottom',style='Campfire'):
    strength=max(0,min(100,float(intensity)))/100
    if strength==0:return frame.copy()
    if style not in STYLES:raise ValueError('Unknown flame style.')
    if color not in COLORS:raise ValueError('Unknown flame color.')
    width,height=frame.size
    # Detail scales with resolution; bound intermediate buffers on very tall media.
    ratio=min(1,1536/width,1536/height)
    size=(max(1,round(width*ratio)),max(1,round(height*ratio)))
    layer=fire_layer(size,phase,strength,color,style)
    if placement=='Top':layer=layer.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    elif placement=='Sides':
        side=layer.rotate(90,expand=True).resize((max(1,size[0]//3),size[1]),Image.Resampling.LANCZOS)
        layer=Image.new('RGBA',size);layer.alpha_composite(side);layer.alpha_composite(side.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(size[0]-side.width,0))
    if layer.size!=frame.size:layer=layer.resize(frame.size,Image.Resampling.LANCZOS)
    result=frame.convert('RGBA');result.alpha_composite(layer);return result.convert('RGB')
