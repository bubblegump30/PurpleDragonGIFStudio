"""Online GIF discovery and bounded downloads, with no embedded credentials."""
import io, json, urllib.request, urllib.parse
from engine import MAX_FRAMES,MAX_PIXELS
from PIL import Image

LIMIT = 25 * 1024 * 1024

def fetch(url, limit=LIMIT):
    if urllib.parse.urlsplit(url).scheme != 'https':
        raise ValueError('Use an HTTPS link to the GIF file itself.')
    request=urllib.request.Request(url,headers={'User-Agent':'PurpleDragonGIFStudio/0.2.0 (desktop GIF editor)'})
    with urllib.request.urlopen(request,timeout=30) as response:
        if urllib.parse.urlsplit(response.url).scheme != 'https': raise ValueError('Insecure redirect refused.')
        data=response.read(limit+1)
    if len(data)>limit: raise ValueError('Download exceeds the 25 MB limit.')
    return data

def search(query, provider='Wikimedia Commons', key='', offset=0, limit=50):
    limit=max(1,min(50,int(limit)));offset=max(0,int(offset))
    query=query.strip()
    if not query: raise ValueError('Enter a search term.')
    if provider=='GIPHY':
        if not key.strip(): raise ValueError('GIPHY search requires your own API key. Use Wikimedia Commons without a key, or Browse GIPHY and paste a direct GIF link.')
        params=urllib.parse.urlencode(dict(api_key=key.strip(),q=query,limit=limit,offset=offset,rating='g'))
        data=json.loads(fetch('https://api.giphy.com/v1/gifs/search?'+params,2*1024*1024))
        return [dict(title=x.get('title') or 'GIF',url=x['images']['original']['url'],source=x['url'],thumbnail=x['images'].get('fixed_width_small',{}).get('url') or x['images']['original']['url']) for x in data.get('data',[]) if x.get('images',{}).get('original',{}).get('url')]
    params=urllib.parse.urlencode(dict(action='query',format='json',generator='search',gsrsearch=query+' filemime:image/gif',gsrnamespace=6,gsrlimit=limit,gsroffset=offset,prop='imageinfo',iiprop='url|mime',iiurlwidth=200))
    data=json.loads(fetch('https://commons.wikimedia.org/w/api.php?'+params,2*1024*1024))
    if 'error' in data: raise ValueError(data['error'].get('info','Search failed.'))
    pages=sorted(data.get('query',{}).get('pages',{}).values(),key=lambda x:x.get('index',0))
    return [dict(title=p['title'].removeprefix('File:'),url=p['imageinfo'][0]['url'],source=p['imageinfo'][0]['descriptionurl'],thumbnail=p['imageinfo'][0].get('thumburl') or p['imageinfo'][0]['url']) for p in pages if p.get('imageinfo') and p['imageinfo'][0].get('mime')=='image/gif']

def decode_gif(data,width):
    frames=[]; durations=[]
    with Image.open(io.BytesIO(data)) as gif:
        if gif.format!='GIF': raise ValueError('This link does not contain a GIF. Paste the direct image URL, not the webpage URL.')
        if gif.n_frames>MAX_FRAMES: raise ValueError('GIF contains more than 300 frames.')
        size=(width,max(1,round(gif.height*width/gif.width)))
        if size[1]>4096: raise ValueError('GIF is too tall. Choose a smaller output width.')
        if gif.n_frames*size[0]*size[1]>MAX_PIXELS:raise ValueError('GIF is too large at this resolution. Reduce output width.')
        from PIL import ImageOps
        for index in range(gif.n_frames):
            gif.seek(index)
            # Pillow composites disposal and transparency while seeking.
            rgba=gif.convert('RGBA'); bg=Image.new('RGBA',rgba.size,'black'); bg.alpha_composite(rgba)
            frames.append(ImageOps.fit(bg.convert('RGB'),size))
            durations.append(max(20,int(gif.info.get('duration',100))))
    return frames,durations

def import_url(url,width):return decode_gif(fetch(url.strip()),width)
