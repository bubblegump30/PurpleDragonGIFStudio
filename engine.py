from pathlib import Path
import shutil, subprocess, tempfile, os
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont

MAX_FRAMES = 300
MAX_PIXELS = 96_000_000

def ffmpeg_path():
    found = shutil.which('ffmpeg')
    if found: return found
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def load_images(paths, width):
    if len(paths) > MAX_FRAMES: raise ValueError('Use at most 300 images.')
    frames = []
    for path in paths:
        with Image.open(path) as source:
            if getattr(source, 'is_animated', False):
                raise ValueError('Import still images or a video. Existing animated GIF editing is not supported yet.')
            source = ImageOps.exif_transpose(source).convert('RGB')
            if not frames:
                size = (width, max(1, round(source.height * width / source.width)))
                if size[1] > 4096: raise ValueError('Output height exceeds 4096 pixels. Choose a smaller width.')
            if (len(frames)+1)*size[0]*size[1]>MAX_PIXELS:raise ValueError('Clip is too large for this resolution. Shorten the clip or reduce output width.')
            frames.append(ImageOps.pad(source, size, color='black'))
    return frames

def load_video(path, start, duration, fps, width):
    if start < 0 or not 0.1 <= duration <= 20: raise ValueError('Choose a start of 0 or greater and a duration between 0.1 and 20 seconds.')
    if duration * fps > MAX_FRAMES: raise ValueError('Limit export to 300 frames. Lower duration or FPS.')
    with tempfile.TemporaryDirectory() as tmp:
        command = [ffmpeg_path(), '-hide_banner', '-loglevel', 'error', '-ss', str(start), '-i', str(path), '-t', str(duration), '-an', '-vf', f'fps={fps},scale={width}:-1', '-frames:v', str(MAX_FRAMES), str(Path(tmp)/'%05d.png')]
        result = subprocess.run(command, capture_output=True, text=True, timeout=120, creationflags=0x08000000 if os.name == 'nt' else 0)
        if result.returncode: raise ValueError(result.stderr[-1800:] or 'Unable to decode this video.')
        frames = load_images(sorted(Path(tmp).glob('*.png')), width)
    if not frames: raise ValueError('No frames found. Check the start time and video format.')
    return frames

def transform(frames, effect='Original', caption='', position='Bottom', reverse=False, pingpong=False, flames=False, flame_intensity=55, flame_color='Orange', flame_placement='Bottom', flame_style='Campfire', caption_font='Sans', caption_size=6, caption_font_path=''):
    if flames and len(frames)==1:
        frames=[frames[0]]*max(2,min(24,MAX_PIXELS//(frames[0].width*frames[0].height)))
    count=len(frames)+(len(frames)-2 if pingpong and len(frames)>2 else 0)
    if frames and count*frames[0].width*frames[0].height>MAX_PIXELS:raise ValueError('Animation is too large at this resolution. Disable ping-pong, shorten it, or reduce width.')
    out = []
    for index, frame in enumerate(frames):
        frame = frame.copy()
        if effect == 'Grayscale': frame = ImageOps.grayscale(frame).convert('RGB')
        elif effect == 'Warm':
            frame = ImageEnhance.Color(frame).enhance(1.35)
            frame = Image.blend(frame, Image.new('RGB', frame.size, '#ff8b28'), .13)
        elif effect == 'Purple': frame = Image.blend(frame, Image.new('RGB', frame.size, '#933cff'), .2)
        elif effect == 'High contrast': frame = ImageEnhance.Contrast(frame).enhance(1.5)
        if flames:
            from flames import overlay
            import math
            frame = overlay(frame, 2*math.pi*index/max(1,len(frames)), flame_intensity, flame_color, flame_placement, flame_style)
        if caption.strip():
            from captions import draw_caption
            draw_caption(frame,caption,position,caption_font,caption_size,caption_font_path)
        out.append(frame)
    if reverse: out.reverse()
    if pingpong and len(out)>2: out += out[-2:0:-1]
    return out

def export_gif(frames, path, fps, speed, colors, loop, durations=None):
    if not frames: raise ValueError('Import media first.')
    delay = max(20, round(1000 / fps / speed / 10) * 10)
    palette_frames = [frame.quantize(colors=colors, method=Image.Quantize.MEDIANCUT) for frame in frames]
    target = Path(path)
    fd, temp = tempfile.mkstemp(suffix='.gif', dir=target.parent)
    os.close(fd)
    try:
        options = dict(save_all=True, append_images=palette_frames[1:], duration=([max(20,round(d/speed/10)*10) for d in durations] if durations else delay), optimize=False, disposal=2)
        if loop: options['loop'] = 0
        palette_frames[0].save(temp, format='GIF', **options)
        os.replace(temp, target)
    finally:
        Path(temp).unlink(missing_ok=True)
    return delay
