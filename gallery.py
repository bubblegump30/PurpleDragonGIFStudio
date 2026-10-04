"""Scrollable search gallery. All Tk operations stay on the UI thread."""
import io
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import ttk
from PIL import Image,ImageOps,ImageTk
from online import fetch,decode_gif

class Gallery(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        self.items=[];self.cards=[];self.selected_index=None;self.generation=0;self.pending=[];self.photos=[]
        self.pool=ThreadPoolExecutor(max_workers=3);self.preview_pool=ThreadPoolExecutor(max_workers=1);self.closed=False;self.preview_frames=[];self.preview_times=[];self.preview_index=0;self.preview_after=None;self.selection_token=0
        self.columnconfigure(0,weight=1);self.rowconfigure(0,weight=1)
        left=ttk.Frame(self);left.grid(row=0,column=0,sticky='nsew',padx=(0,12))
        self.scroll=tk.Canvas(left,bg='#0d0a14',highlightthickness=0,width=540,height=320)
        scrollbar=ttk.Scrollbar(left,orient='vertical',command=self.scroll.yview)
        scrollbar.pack(side='right',fill='y');self.scroll.pack(side='left',fill='both',expand=True);self.scroll.configure(yscrollcommand=scrollbar.set)
        self.inner=ttk.Frame(self.scroll);self.window=self.scroll.create_window(0,0,window=self.inner,anchor='nw')
        self.inner.bind('<Configure>',lambda e:self.scroll.configure(scrollregion=self.scroll.bbox('all')))
        self.scroll.bind('<Configure>',self.resize)
        self.details=ttk.Frame(self,width=260);self.details.grid(row=0,column=1,sticky='ns');self.details.grid_propagate(False)
        self.details.columnconfigure(0,weight=1)
        ttk.Label(self.details,text='SELECTED GIF',foreground='#c48aff',font=('Segoe UI',12,'bold')).grid(row=0,column=0,pady=8)
        self.preview=tk.Label(self.details,bg='#0d0a14',fg='#c3b0d4',text='Select a thumbnail',width=28,height=12)
        self.preview.grid(row=1,column=0,sticky='ew')
        self.title=ttk.Label(self.details,text='',wraplength=240,anchor='center',justify='center');self.title.grid(row=2,column=0,padx=6,pady=8)
        self.info=ttk.Label(self.details,text='',wraplength=240,justify='center');self.info.grid(row=3,column=0,padx=6,pady=4)
        self.details.rowconfigure(6,weight=1)
        self.bind('<Destroy>',self.destroyed,add='+');self.after(60,self.poll)
        self.bind_wheel(self.scroll);self.bind_wheel(self.inner)
    def bind_wheel(self,widget):
        def wheel(e):
            delta=-1 if getattr(e,'num',0)==4 or e.delta>0 else 1
            self.scroll.yview_scroll(delta*3,'units');return 'break'
        for event in ['<MouseWheel>','<Button-4>','<Button-5>']:widget.bind(event,wheel)
    def resize(self,event):
        self.scroll.itemconfigure(self.window,width=event.width)
        columns=max(1,event.width//180)
        for i,card in enumerate(self.cards):card.grid(row=i//columns,column=i%columns,padx=5,pady=5,sticky='nsew')
        for i in range(10):self.inner.columnconfigure(i,weight=1 if i<columns else 0)
    def submit(self,fn,done,preview=False):self.pending.append(((self.preview_pool if preview else self.pool).submit(fn),self.generation,done))
    def poll(self):
        if self.closed:return
        waiting=[]
        for future,generation,done in self.pending:
            if not future.done():waiting.append((future,generation,done));continue
            if generation!=self.generation:continue
            try:done(future.result(),None)
            except Exception as exc:done(None,exc)
        self.pending=waiting;self.after(60,self.poll)
    def set_items(self,items):
        self.generation+=1;self.selection_token+=1
        for future,_,_ in self.pending:future.cancel()
        self.stop_animation();self.items=items;self.selected_index=None;self.photos=[]
        for card in self.cards:card.destroy()
        self.cards=[];self.scroll.yview_moveto(0)
        self.preview.configure(image='',text='Select a thumbnail');self.title.configure(text='');self.info.configure(text='')
        for i,item in enumerate(items):
            card=tk.Frame(self.inner,bg='#1d1428',highlightbackground='#49305e',highlightthickness=2,takefocus=True)
            image_label=tk.Label(card,bg='#0d0a14',fg='#bdb1ce',text='Loading preview…',width=20,height=7)
            image_label.pack(fill='both',expand=True,padx=5,pady=5)
            title=tk.Label(card,text=item['title'],bg='#1d1428',fg='#f4effa',wraplength=155,height=3,font=('Segoe UI',11),justify='center');title.pack(fill='x',padx=4,pady=(0,4))
            for widget in (card,image_label,title):
                widget.bind('<Button-1>',lambda e,index=i:self.select(index));self.bind_wheel(widget)
            card.bind('<Return>',lambda e,index=i:self.select(index));card.bind('<space>',lambda e,index=i:self.select(index))
            self.cards.append(card)
            def thumbnail(item=item):
                data=fetch(item.get('thumbnail') or item['url'],6*1024*1024)
                with Image.open(io.BytesIO(data)) as im:return ImageOps.pad(im.convert('RGB'),(160,110),color='#0d0a14')
            def loaded(image,error,label=image_label):
                if error:label.configure(text='Preview unavailable\nClick to retry full GIF');return
                photo=ImageTk.PhotoImage(image);self.photos.append(photo);label.configure(image=photo,text='',width=160,height=110)
            self.submit(thumbnail,loaded)
        self.resize(type('Size',(),{'width':max(180,self.scroll.winfo_width())})())
    def selected(self):return self.items[self.selected_index] if self.selected_index is not None else None
    def stop_animation(self):
        if self.preview_after is not None:
            self.after_cancel(self.preview_after);self.preview_after=None
        self.preview_frames=[]
    def select(self,index):
        self.selected_index=index;self.cards[index].focus_set();self.selection_token+=1;token=self.selection_token;self.stop_animation()
        for n,card in enumerate(self.cards):card.configure(highlightbackground='#c68aff' if n==index else '#49305e')
        item=self.items[index];self.title.configure(text=item['title']);self.preview.configure(image='',text='Loading animation…');self.info.configure(text='')
        def load():return decode_gif(fetch(item['url']),240)
        def ready(result,error):
            if token!=self.selection_token:return
            if error:self.preview.configure(image='',text='Preview unavailable');self.info.configure(text=str(error)[:220]);return
            frames,durations=result
            self.preview_frames=[ImageTk.PhotoImage(ImageOps.pad(frame,(240,180),color='#0d0a14')) for frame in frames]
            self.preview_times=durations;self.preview_index=0;self.info.configure(text=f'{len(frames)} frames • {sum(durations)/1000:.2f} seconds');self.animate()
        self.submit(load,ready,preview=True)
    def animate(self):
        if self.closed or not self.preview_frames:return
        index=self.preview_index;self.preview.configure(image=self.preview_frames[index],text='',width=240,height=180)
        self.preview_index=(index+1)%len(self.preview_frames)
        self.preview_after=self.after(self.preview_times[index],self.animate)
    def destroyed(self,event):
        if event.widget!=self:return
        self.closed=True
        if self.preview_after is not None:self.after_cancel(self.preview_after)
        for future,_,_ in self.pending:future.cancel()
        self.pool.shutdown(wait=False,cancel_futures=True);self.preview_pool.shutdown(wait=False,cancel_futures=True)
