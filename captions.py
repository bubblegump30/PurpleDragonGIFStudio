"""Caption fonts and emoji fallback for Pillow exports."""
import os
from pathlib import Path
from PIL import ImageDraw, ImageFont
PRESETS={'Sans':'arial.ttf','Bold':'arialbd.ttf','Serif':'times.ttf','Monospace':'consola.ttf','Handwritten':'comic.ttf','Impact':'impact.ttf'}
EMOJIS=['😀','😂','😍','😎','😭','😡','👍','👎','👏','🙏','🔥','❤️','⭐','✨','🎉','💜','🎵','🎮','🚀','💯','👑','💀','🐉','⚡']
def font_path(name):
    path=Path(name)
    if path.is_file():return str(path)
    windows=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/name
    return str(windows) if windows.is_file() else name

def load_fonts(style,size,custom=''):
    if custom:
        try:main=ImageFont.truetype(custom,size)
        except OSError:raise ValueError('Cannot open the custom font. Choose a valid TTF or OTF file.')
    else:
        name=PRESETS.get(style,PRESETS['Sans'])
        fallback={'Bold':'DejaVuSans-Bold.ttf','Serif':'DejaVuSerif.ttf','Monospace':'DejaVuSansMono.ttf'}.get(style,'DejaVuSans.ttf')
        try:main=ImageFont.truetype(font_path(name),size)
        except OSError:
            try:main=ImageFont.truetype(fallback,size)
            except OSError:main=ImageFont.load_default(size=size)
    try:emoji=ImageFont.truetype(font_path('seguiemj.ttf'),size)
    except OSError:emoji=main
    return main,emoji

def draw_caption(frame,text,position='Bottom',style='Sans',size_percent=6,custom=''):
    size=max(12,round(frame.width*float(size_percent)/100))
    main,emoji=load_fonts(style,size,custom);draw=ImageDraw.Draw(frame)
    def choose(char):return emoji if ord(char)>=0x1f000 or 0x2600<=ord(char)<=0x27ff else main
    lines=[];line=[];width=0;available=max(1,frame.width-24)
    for char in text.strip()[:200]:
        if char=='\ufe0f':continue # monochrome outline emoji avoid unsupported color-only strikes
        font=choose(char);advance=0 if char=="\n" else draw.textlength(char,font=font)
        if char=='\n' or (width+advance>available and line):
            lines.append((line,width));line=[];width=0
        if char!='\n':line.append((char,font,advance));width+=advance
    if line:lines.append((line,width))
    line_height=size+8;height=len(lines)*line_height
    y=12 if position=='Top' else max(4,frame.height-height-12)
    for line,width in lines:
        x=(frame.width-width)/2
        for char,font,advance in line:
            draw.text((x,y+size),char,font=font,anchor='ls',fill='white',stroke_width=2,stroke_fill='black');x+=advance
        y+=line_height
