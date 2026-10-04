import tkinter as tk
from tkinter import ttk, filedialog
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import webbrowser, urllib.parse
from PIL import ImageTk, ImageOps
from gallery import Gallery
from credentials import KeyStore
from captions import PRESETS, EMOJIS
from flames import COLORS, STYLES
from engine import load_images, load_video, transform, export_gif
from online import search, import_url, decode_gif

class Studio:
    def __init__(self, root):
        self.root=root;self.frames=[];self.preview=[];self.durations=None;self.preview_durations=None
        self.index=0;self.playing=False;self.busy=False;self.closed=False
        self.pool=ThreadPoolExecutor(max_workers=1);self.actions=[]
        root.title('Purple Dragon GIF Studio • v0.6.1')
        width=min(1380,max(1000,root.winfo_screenwidth()-80));height=min(900,max(700,root.winfo_screenheight()-100))
        root.geometry(f'{width}x{height}');root.minsize(1000,700);root.configure(bg='#09070f')
        self.style=ttk.Style(root);self.style.theme_use('clam')
        self.style.configure('.',background='#17111f',foreground='#f4effa',font=('Segoe UI',12))
        self.style.configure('TFrame',background='#17111f')
        self.style.configure('TLabel',background='#17111f',foreground='#f4effa')
        self.style.configure('TLabelframe',background='#17111f',bordercolor='#59416e')
        self.style.configure('TLabelframe.Label',foreground='#c591ff',font=('Segoe UI',12,'bold'))
        self.style.configure('TButton',padding=(14,11),background='#30223e',foreground='#f4effa',bordercolor='#6d4c88')
        self.style.map('TButton',background=[('disabled','#211b29'),('active','#58347a')],foreground=[('disabled','#a89ab4')])
        self.style.configure('Primary.TButton',background='#7835b6',font=('Segoe UI',12,'bold'))
        self.style.map('Primary.TButton',background=[('disabled','#3b264b'),('active','#964ada')])
        self.style.configure('Emoji.TButton',font=('Segoe UI Emoji',16),padding=(7,8))
        self.style.configure('TEntry',fieldbackground='#0e0a15',foreground='#f4effa',padding=8,insertcolor='#ffffff')
        self.style.configure('TCombobox',fieldbackground='#0e0a15',foreground='#f4effa',padding=7,arrowcolor='#f4effa')
        self.style.map('TCombobox',fieldbackground=[('readonly','#0e0a15')],foreground=[('readonly','#f4effa')],selectbackground=[('readonly','#0e0a15')],selectforeground=[('readonly','#f4effa')])
        self.style.configure('TCheckbutton',padding=7)
        self.style.configure('TNotebook',background='#09070f',borderwidth=0)
        self.style.configure('TNotebook.Tab',padding=(24,13),background='#241a30',font=('Segoe UI',12,'bold'))
        self.style.map('TNotebook.Tab',background=[('selected','#60318a')],foreground=[('selected','#ffffff')])
        self.style.configure('Horizontal.TProgressbar',background='#a970ff',troughcolor='#0e0a15')
        root.option_add('*TCombobox*Listbox.background','#1d172b');root.option_add('*TCombobox*Listbox.foreground','#f4effa')
        root.option_add('*TCombobox*Listbox.selectBackground','#65428a');root.option_add('*TCombobox*Listbox.selectForeground','#ffffff')
        root.option_add('*TCombobox*Listbox.font',('Segoe UI',12))
        self.vars={name:tk.StringVar(value=value) for name,value in [('Width','480'),('FPS','12'),('Speed','1'),('Colors','256'),('Effect','Original'),('Caption position','Bottom'),('Flame color','Orange'),('Flame placement','Bottom'),('Flame style','Campfire')]}
        self.caption_font=tk.StringVar(value='Sans');self.caption_size=tk.StringVar(value='6');self.caption_font_path='';self.custom_font_label=tk.StringVar(value='No custom font selected');self.search_context=None;self.search_offset=0
        self.caption=tk.StringVar();self.reverse=tk.BooleanVar();self.ping=tk.BooleanVar();self.loop=tk.BooleanVar(value=True)
        self.flames=tk.BooleanVar();self.flame_intensity=tk.DoubleVar(value=55)
        self.stats={name:tk.StringVar(value='—') for name in ['FRAMES','DURATION','DIMENSIONS']}
        self.status=tk.StringVar(value='Ready — import a video, GIF, or still images to begin.')
        self.play_label=tk.StringVar(value='Play preview');self.clip_path=None;self.clip_start=tk.StringVar(value='0');self.clip_duration=tk.StringVar(value='3')
        self.clip_name=tk.StringVar(value='No video selected')
        title=ttk.Frame(root,padding=(20,15));title.pack(fill='x')
        ttk.Label(title,text='PURPLE DRAGON GIF STUDIO',font=('Segoe UI',20,'bold'),anchor='center').pack(fill='x')
        ttk.Label(title,text='Create GIFs • Browse animations • Add moving flame effects',anchor='center',foreground='#bca8ce').pack(fill='x',pady=(5,0))
        self.tabs=ttk.Notebook(root);self.tabs.pack(fill='both',expand=True,padx=18)
        self.editor=ttk.Frame(self.tabs,padding=14);self.search_page=ttk.Frame(self.tabs,padding=14);self.export_page=ttk.Frame(self.tabs,padding=20)
        self.tabs.add(self.editor,text='Editor & Preview');self.tabs.add(self.search_page,text='Find Online GIFs');self.tabs.add(self.export_page,text='Output Settings')
        self.build_editor();self.build_search();self.build_output()
        footer=ttk.Frame(root,padding=(20,10));footer.pack(side='bottom',fill='x',before=self.tabs)
        self.status_label=ttk.Label(footer,textvariable=self.status,wraplength=1250);self.status_label.pack(fill='x')
        self.progress=ttk.Progressbar(footer,mode='indeterminate');self.progress.pack(fill='x',pady=(7,0))
        root.bind('<Configure>',lambda e:self.status_label.configure(wraplength=max(400,root.winfo_width()-40)) if e.widget==root else None);root.protocol('WM_DELETE_WINDOW',self.close);root.after(80,self.tick)
        root.bind('<Control-o>',lambda e:self.images());root.bind('<Control-s>',lambda e:self.export())
    def button(self,parent,text,command,primary=False,**pack):
        b=ttk.Button(parent,text=text,command=command,style='Primary.TButton' if primary else 'TButton')
        self.actions.append(b)
        if pack:b.pack(**pack)
        return b
    def field(self,parent,label,var,values=None):
        ttk.Label(parent,text=label).pack(anchor='w',pady=(10,4))
        if values:ttk.Combobox(parent,textvariable=var,values=values,state='readonly').pack(fill='x')
        else:ttk.Entry(parent,textvariable=var).pack(fill='x')
    def build_editor(self):
        imports=ttk.Frame(self.editor);imports.pack(fill='x',pady=(0,8))
        for label,command in [('Import Video',self.video),('Import GIF',self.saved_gif),('Import Images',self.images),('Find Online GIFs',self.online)]:self.button(imports,label,command,side='left',padx=(0,8))
        self.clip=ttk.Labelframe(self.editor,text='Video clip',padding=10)
        ttk.Label(self.clip,textvariable=self.clip_name).grid(row=0,column=0,columnspan=5,sticky='w',pady=(0,5))
        ttk.Label(self.clip,text='Start (seconds)').grid(row=1,column=0,sticky='w',padx=5)
        ttk.Entry(self.clip,textvariable=self.clip_start,width=8).grid(row=1,column=1,padx=5)
        ttk.Label(self.clip,text='Duration (seconds)').grid(row=1,column=2,padx=5)
        ttk.Entry(self.clip,textvariable=self.clip_duration,width=8).grid(row=1,column=3,padx=5)
        self.button(self.clip,'Load Video Clip',self.load_clip,True).grid(row=1,column=4,padx=8)
        body=ttk.Frame(self.editor);body.pack(fill='both',expand=True)
        self.editor_body=body
        preview_area=ttk.Frame(body);preview_area.pack(side='left',fill='both',expand=True,padx=(0,14))
        statrow=ttk.Frame(preview_area);statrow.pack(fill='x',pady=(0,8))
        for name in self.stats:
            card=ttk.Labelframe(statrow,text=name.title(),padding=8);card.pack(side='left',fill='x',expand=True,padx=(0,6))
            ttk.Label(card,textvariable=self.stats[name],font=('Segoe UI',16,'bold'),foreground='#dbb6ff').pack()
        self.media=ttk.Label(preview_area,text='Your imported media and applied preview details appear here.',wraplength=560);self.media.pack(fill='x',pady=6)
        self.canvas=tk.Label(preview_area,bg='#0b0811',fg='#c5b4d4',text='Your animated preview appears here',font=('Segoe UI',15),anchor='center')
        self.canvas.pack(fill='both',expand=True,pady=8)
        row=ttk.Frame(preview_area);row.pack(side='bottom',fill='x',before=self.canvas)
        self.play_button=self.button(row,'Play preview',self.toggle,side='left',padx=(0,8));self.play_button.configure(textvariable=self.play_label)
        self.button(row,'Apply Changes',self.apply,True,side='left',padx=(0,8))
        self.button(row,'Export GIF',self.export,True,side='right')
        sidebar=ttk.Frame(body);sidebar.pack(side='right',fill='y')
        scroll=tk.Canvas(sidebar,bg='#17111f',highlightthickness=0,width=330)
        bar=ttk.Scrollbar(sidebar,orient='vertical',command=scroll.yview);bar.pack(side='right',fill='y');scroll.pack(side='left',fill='both',expand=True)
        scroll.configure(yscrollcommand=bar.set);form=ttk.Frame(scroll,padding=(10,0,10,10));window=scroll.create_window(0,0,window=form,anchor='nw')
        scroll.bind('<Configure>',lambda e:scroll.itemconfigure(window,width=e.width));form.bind('<Configure>',lambda e:scroll.configure(scrollregion=scroll.bbox('all')))
        ttk.Label(form,text='Effects & Animation',font=('Segoe UI',14,'bold'),foreground='#c591ff').pack(anchor='w',pady=8)
        ttk.Checkbutton(form,text='Enable moving flames',variable=self.flames).pack(anchor='w')
        for label,values in [('Flame style',STYLES),('Flame color',COLORS),('Flame placement',['Bottom','Top','Sides'])]:self.field(form,label,self.vars[label],values)
        ttk.Label(form,text='Flame intensity').pack(anchor='w',pady=(12,0))
        self.intensity_text=tk.StringVar(value='55%');ttk.Label(form,textvariable=self.intensity_text).pack(anchor='e')
        self.flame_intensity.trace_add('write',lambda *args:self.intensity_text.set(f'{self.flame_intensity.get():.0f}%'))
        ttk.Scale(form,from_=0,to=100,variable=self.flame_intensity).pack(fill='x',pady=5)
        self.field(form,'Color effect',self.vars['Effect'],['Original','Grayscale','Warm','Purple','High contrast'])
        self.field(form,'Caption',self.caption);self.field(form,'Caption position',self.vars['Caption position'],['Top','Bottom'])
        self.field(form,'Caption font style',self.caption_font,list(PRESETS))
        self.field(form,'Caption size (% of image width)',self.caption_size,['3','4','5','6','8','10','12'])
        self.button(form,'Choose Custom Font',self.choose_font,side='top',fill='x',pady=6)
        self.button(form,'Use Selected Font Style',self.reset_font,side='top',fill='x')
        ttk.Label(form,textvariable=self.custom_font_label,wraplength=280).pack(fill='x',pady=4)
        ttk.Label(form,text='Add emoji to caption',foreground='#c591ff').pack(anchor='w',pady=(10,4))
        emoji_grid=ttk.Frame(form);emoji_grid.pack(fill='x')
        for i,emoji in enumerate(EMOJIS):
            b=self.button(emoji_grid,emoji,lambda value=emoji:self.caption.set(self.caption.get()+value))
            b.configure(style='Emoji.TButton')
            b.grid(row=i//4,column=i%4,sticky='ew',padx=2,pady=2)
        for column in range(4):emoji_grid.columnconfigure(column,weight=1)
        for text,var in [('Reverse animation',self.reverse),('Ping-pong loop',self.ping)]:ttk.Checkbutton(form,text=text,variable=var).pack(anchor='w',pady=4)
        ttk.Label(form,text='Apply Changes refreshes the preview. Export uses the current settings.',wraplength=280,foreground='#bca8ce').pack(fill='x',pady=12)
        def wheel(e):scroll.yview_scroll(-3 if e.delta>0 or e.num==4 else 3,'units');return 'break'
        def bind_wheel(widget):
            for event in ['<MouseWheel>','<Button-4>','<Button-5>']:widget.bind(event,wheel,add='+')
            for child in widget.winfo_children():bind_wheel(child)
        bind_wheel(sidebar)
    def build_output(self):
        scroll=tk.Canvas(self.export_page,bg='#17111f',highlightthickness=0)
        bar=ttk.Scrollbar(self.export_page,orient='vertical',command=scroll.yview)
        bar.pack(side='right',fill='y');scroll.pack(side='left',fill='both',expand=True);scroll.configure(yscrollcommand=bar.set)
        content=ttk.Frame(scroll,padding=(0,0,10,10));window=scroll.create_window(0,0,window=content,anchor='nw')
        scroll.bind('<Configure>',lambda e:scroll.itemconfigure(window,width=e.width))
        content.bind('<Configure>',lambda e:scroll.configure(scrollregion=scroll.bbox('all')))
        ttk.Label(content,text='Output Settings',font=('Segoe UI',17,'bold'),foreground='#c591ff').pack(anchor='w',pady=(0,8))
        form=ttk.Frame(content);form.pack(fill='x')
        choices={'Width':['240','320','480','640','800','1280','1920','3840'],'FPS':['6','10','12','15','20','24'],'Speed':['0.5','0.75','1','1.5','2'],'Colors':['64','128','256']}
        for row,(label,values) in enumerate(choices.items()):
            ttk.Label(form,text={'Width':'Output width (pixels)','FPS':'Frames per second','Speed':'Playback speed','Colors':'GIF palette colors'}[label]).grid(row=row,column=0,sticky='w',padx=(0,24),pady=12)
            ttk.Combobox(form,textvariable=self.vars[label],values=values,state='readonly',width=24).grid(row=row,column=1,sticky='w')
        ttk.Checkbutton(content,text='Loop exported GIF forever',variable=self.loop).pack(anchor='w',pady=15)
        ttk.Label(content,text='Choose width and video FPS before importing. Reimport to change source dimensions or video sampling. Speed affects every source type. Imported GIFs preserve their original timing.\n\n4K needs short clips. The 96-million-pixel budget protects memory; reduce width or duration if a clip exceeds it.',wraplength=850,justify='left').pack(anchor='w',pady=12)
        about=ttk.Labelframe(content,text='About Purple Dragon GIF Studio',padding=16)
        about.pack(fill='x',pady=(16,12))
        ttk.Label(about,text='Created by Purple Dragon Foundation Ltd',font=('Segoe UI',14,'bold'),foreground='#d5a7ff').pack(anchor='w',pady=(0,10))
        links=ttk.Frame(about);links.pack(fill='x')
        for label,url in [('Visit Website','https://www.purpledragonfoundationltd.xyz/'),('GitHub · bubblegump30','https://github.com/bubblegump30'),('Donate via PayPal','https://www.paypal.com/paypalme/KyleAustin85')]:
            self.button(links,label,lambda target=url:webbrowser.open(target),side='left',padx=(0,10),pady=4)
        ttk.Label(about,text='Donations help support development. Thank you for your support.',wraplength=850,foreground='#bca8ce').pack(anchor='w',pady=(8,0))
        self.button(content,'Return to Editor',self.open_preview,side='left',padx=(0,12),pady=10)
        self.button(content,'Export GIF',self.export,True,side='left',pady=10)
    def build_search(self):
        top=ttk.Frame(self.search_page);top.pack(fill='x')
        self.query=tk.StringVar();self.provider=tk.StringVar(value='Wikimedia Commons');self.key=tk.StringVar();self.url=tk.StringVar()
        ttk.Label(top,text='Search GIFs').grid(row=0,column=0,sticky='w',pady=4)
        self.query_entry=ttk.Entry(top,textvariable=self.query);self.query_entry.grid(row=1,column=0,sticky='ew',padx=(0,8))
        self.query_entry.bind('<Return>',lambda e:self.do_search())
        ttk.Combobox(top,textvariable=self.provider,values=['Wikimedia Commons','GIPHY'],state='readonly',width=22).grid(row=1,column=1,padx=(0,8))
        self.button(top,'Search',self.do_search,True).grid(row=1,column=2)
        ttk.Label(top,text='GIPHY API key (optional; save securely for future launches)').grid(row=2,column=0,columnspan=3,sticky='w',pady=(8,3))
        ttk.Entry(top,textvariable=self.key,show='*').grid(row=3,column=0,columnspan=2,sticky='ew',padx=(0,8))
        self.button(top,'Browse GIPHY',lambda:webbrowser.open('https://giphy.com/search/'+urllib.parse.quote(self.query.get(),safe=''))).grid(row=3,column=2)
        self.key_store=KeyStore();self.remember_key=tk.BooleanVar();self.key_status=tk.StringVar()
        key_controls=ttk.Frame(top);key_controls.grid(row=4,column=0,columnspan=3,sticky='ew',pady=(8,0))
        ttk.Checkbutton(key_controls,text='Remember API key',variable=self.remember_key,command=self.remember_changed).pack(side='left',padx=(0,10))
        self.button(key_controls,'Save API Key',self.save_key,side='left',padx=(0,8))
        self.button(key_controls,'Forget Saved Key',self.forget_key,side='left')
        ttk.Label(top,textvariable=self.key_status,wraplength=850).grid(row=5,column=0,columnspan=3,sticky='w',pady=5)
        try:
            saved=self.key_store.load()
            if saved:self.key.set(saved);self.remember_key.set(True);self.key_status.set('Saved key loaded securely for your Windows account.')
            else:self.key_status.set('Key is not saved. Enable Remember API key to keep it between launches.')
        except Exception:self.key_status.set('Could not unlock the saved key. Enter a new key or forget the saved key.')
        top.columnconfigure(0,weight=1)
        self.button(top,'Load More (50)',self.load_more).grid(row=6,column=0,sticky='w',pady=5)
        self.gallery=Gallery(self.search_page);self.gallery.pack(fill='both',expand=True,pady=10)
        self.button(self.gallery.details,'Import Selected GIF',self.import_selected,True).grid(row=4,column=0,sticky='ew',padx=6,pady=8)
        self.button(self.gallery.details,'View Source / License',self.source).grid(row=5,column=0,sticky='ew',padx=6,pady=4)
        self.search_state=tk.StringVar(value='Commons needs no key. Search, select a thumbnail, then import it.')
        ttk.Label(self.search_page,textvariable=self.search_state,wraplength=900).pack(fill='x',pady=3)
        links=ttk.Frame(self.search_page);links.pack(fill='x',pady=(6,0));ttk.Label(links,text='Direct GIF URL').pack(side='left',padx=(0,10))
        ttk.Entry(links,textvariable=self.url).pack(side='left',fill='x',expand=True,padx=(0,8));self.button(links,'Import URL',lambda:self.download(self.url.get()),side='right')
    def save_key(self):
        try:self.key_store.save(self.key.get())
        except Exception as exc:self.key_status.set(str(exc));return False
        self.remember_key.set(True);self.key_status.set('API key saved securely for your Windows account.');return True
    def forget_key(self):
        try:self.key_store.forget()
        except Exception:self.key_status.set('Could not remove the saved key. Try again.');return False
        self.remember_key.set(False);self.key.set('');self.key_status.set('Saved key removed. Enter a key to use GIPHY.');return True
    def remember_changed(self):
        if self.remember_key.get():
            if self.key.get().strip():
                if not self.save_key():self.remember_key.set(False)
            else:self.key_status.set('Enter a key, then click Save API Key or Search to remember it.')
        else:
            try:self.key_store.forget();self.key_status.set('Key will be used only for this session.')
            except Exception:self.remember_key.set(True);self.key_status.set('Could not remove the saved key. Try again.')
    def import_menu(self):self.open_preview()
    def open_preview(self):self.tabs.select(self.editor);self.root.after_idle(self.show)
    def preferences(self):self.open_preview()
    def online(self):self.tabs.select(self.search_page);self.query_entry.focus_set()
    def choose_font(self):
        path=filedialog.askopenfilename(parent=self.root,filetypes=[('Fonts','*.ttf *.otf')])
        if path:self.caption_font_path=path;self.custom_font_label.set(Path(path).name)
    def reset_font(self):
        self.caption_font_path='';self.custom_font_label.set('No custom font selected')
    def do_search(self):self.search_page_results(False)
    def load_more(self):self.search_page_results(True)
    def search_page_results(self,append):
        if self.busy:return
        if self.remember_key.get() and self.key.get().strip() and not self.save_key():return
        context=(self.query.get().strip(),self.provider.get(),self.key.get())
        if append and (self.search_context is None or context!=self.search_context):
            self.search_state.set('Run Search first after changing the query or provider.');return
        offset=self.search_offset if append else 0
        self.search_state.set('Loading more GIFs…' if append else 'Searching…')
        def found(items):
            old=list(self.gallery.items) if append else []
            urls={item['url'] for item in old}
            old.extend(item for item in items if item['url'] not in urls)
            self.gallery.set_items(old);self.search_context=context;self.search_offset=offset+50
            self.search_state.set(f'{len(old)} GIFs loaded — Load More adds the next 50 results.' if items else f'{len(old)} GIFs loaded. No results on this page.')
        self.run(lambda:search(*context,offset=offset,limit=50),found)
    def download(self,url):
        if self.busy:return
        width=int(self.vars['Width'].get());self.run(lambda:import_url(url,width),self.gif_loaded)
    def import_selected(self):
        item=self.gallery.selected()
        if item:self.download(item['url'])
        else:self.search_state.set('Select a thumbnail first.')
    def source(self):
        item=self.gallery.selected()
        if item:webbrowser.open(item['source'])
    def close(self):
        if self.busy:self.status.set('An operation is in progress. Wait for it to finish before closing.');return
        self.closed=True;self.pool.shutdown(wait=False,cancel_futures=True);self.root.destroy()
    def run(self,fn,done):
        if self.busy:return
        self.busy=True;self.playing=False;self.play_label.set('Play preview');self.progress.start();self.status.set('Working…')
        for button in self.actions:button.state(['disabled'])
        future=self.pool.submit(fn)
        def poll():
            if self.closed:return
            if not future.done():self.root.after(80,poll);return
            self.busy=False;self.progress.stop()
            for button in self.actions:button.state(['!disabled'])
            try:result=future.result()
            except Exception as exc:self.status.set(f'Error: {exc}');return
            self.status.set('Ready')
            try:done(result)
            except Exception as exc:self.status.set(f'Error: {exc}')
        self.root.after(80,poll)
    def settings(self):
        return dict(caption_font=self.caption_font.get(),caption_size=float(self.caption_size.get()),caption_font_path=self.caption_font_path,effect=self.vars['Effect'].get(),caption=self.caption.get(),position=self.vars['Caption position'].get(),reverse=self.reverse.get(),pingpong=self.ping.get(),flames=self.flames.get(),flame_intensity=self.flame_intensity.get(),flame_color=self.vars['Flame color'].get(),flame_placement=self.vars['Flame placement'].get(),flame_style=self.vars['Flame style'].get())
    def loaded(self,frames):
        self.durations=None; self.frames=frames; self.open_preview(); self.apply(); self.media.configure(text=f'{len(frames)} source frames • {frames[0].width} × {frames[0].height} • Reimport to change width or source FPS')
    def adjust_durations(self,options):
        if not self.durations:return None
        result=list(self.durations)
        if options['flames'] and len(result)==1:
            from engine import MAX_PIXELS
            result*=max(2,min(24,MAX_PIXELS//(self.frames[0].width*self.frames[0].height)))
        if options['reverse']:result.reverse()
        if options['pingpong'] and len(result)>2:result+=result[-2:0:-1]
        return result
    def gif_loaded(self,result):
        self.frames,self.durations=result
        self.media.configure(text=f'{len(self.frames)} GIF frames • Original timing preserved • FPS applies to videos and still images')
        self.open_preview();self.apply()
    def saved_gif(self):
        if self.busy:return
        path=filedialog.askopenfilename(parent=self.root,filetypes=[('GIF','*.gif')])
        if path:
            width=int(self.vars['Width'].get());self.run(lambda:decode_gif(Path(path).read_bytes(),width),self.gif_loaded)
    def images(self):
        if self.busy:return
        paths=filedialog.askopenfilenames(parent=self.root,filetypes=[('Still images','*.png *.jpg *.jpeg *.webp *.bmp')])
        if paths:
            width=int(self.vars['Width'].get());self.run(lambda:load_images(paths,width),self.loaded)
    def video(self):
        if self.busy:return
        path=filedialog.askopenfilename(parent=self.root,filetypes=[('Videos','*.mp4 *.mov *.mkv *.avi *.webm')])
        if not path:return
        self.clip_path=path;self.clip_name.set(Path(path).name);self.open_preview()
        self.clip.pack(fill='x',pady=(0,10),before=self.editor_body)
        self.status.set('Set start and duration in the Video clip panel, then click Load Video Clip.')
    def load_clip(self):
        if self.busy:return
        if not self.clip_path:self.status.set('Import a video first.');return
        try:start=float(self.clip_start.get());duration=float(self.clip_duration.get())
        except ValueError:self.status.set('Error: video start and duration must be numeric.');return
        path=self.clip_path;fps=int(self.vars['FPS'].get());width=int(self.vars['Width'].get())
        self.run(lambda:load_video(path,start,duration,fps,width),self.loaded)
    def apply(self):
        if self.busy:return
        if not self.frames:self.status.set('Import media before applying effects.');return
        options=self.settings();timing=self.adjust_durations(options)
        self.run(lambda:transform(self.frames,**options),lambda frames:self.applied(frames,timing))
    def applied(self,frames,timing=None):
        self.preview=frames;self.preview_durations=timing;self.index=0;self.playing=True;self.play_label.set('Pause preview')
        self.update_stats();self.show();self.status.set(f'Preview updated — {len(frames)} frames. Export GIF uses your current settings.')
    def update_stats(self):
        if not self.preview:return
        self.stats['FRAMES'].set(str(len(self.preview)))
        duration=(sum(self.preview_durations)/1000 if self.preview_durations else len(self.preview)/int(self.vars['FPS'].get()))/float(self.vars['Speed'].get())
        self.stats['DURATION'].set(f'{duration:.2f} s');self.stats['DIMENSIONS'].set(f'{self.preview[0].width} × {self.preview[0].height}')
    def show(self):
        if not self.preview or not self.canvas.winfo_ismapped():return
        size=(max(1,self.canvas.winfo_width()-20),max(1,self.canvas.winfo_height()-20))
        self.photo=ImageTk.PhotoImage(ImageOps.contain(self.preview[self.index],size));self.canvas.configure(image=self.photo,text='')
    def toggle(self):
        if not self.preview:self.status.set('Import media to start a preview.');return
        self.playing=not self.playing;self.play_label.set('Pause preview' if self.playing else 'Play preview')
    def tick(self):
        if self.closed:return
        delay=max(20,round(1000/int(self.vars['FPS'].get())/float(self.vars['Speed'].get())/10)*10)
        if self.playing and self.preview and not self.busy:
            self.index=(self.index+1)%len(self.preview)
            if self.tabs.select()==str(self.editor):self.show()
        if self.preview_durations and self.preview:delay=max(20,round(self.preview_durations[self.index]/float(self.vars['Speed'].get())/10)*10)
        self.root.after(delay,self.tick)
    def export(self):
        if self.busy:return
        if not self.frames:self.status.set('Import media before exporting.');return
        path=filedialog.asksaveasfilename(parent=self.root,defaultextension='.gif',filetypes=[('Animated GIF','*.gif')])
        if not path:return
        options=self.settings();fps=int(self.vars['FPS'].get());speed=float(self.vars['Speed'].get());colors=int(self.vars['Colors'].get());loop=self.loop.get();durations=self.adjust_durations(options)
        def work():return export_gif(transform(self.frames,**options),path,fps,speed,colors,loop,durations)
        self.run(work,lambda _:self.status.set(f'Saved GIF: {path}'))
if __name__=='__main__':
    # Opt in before any Tk window is created so Windows does not bitmap-scale text.
    import sys
    if sys.platform == 'win32':
        import ctypes
        try:
            if not ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            try: ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError): pass
    root=tk.Tk(); Studio(root); root.mainloop()
