import os, sys, re, json, csv, html, time, shutil, threading, webbrowser, urllib.parse, base64, mimetypes, subprocess
from pathlib import Path
from urllib.request import Request, urlopen
from tkinter import Tk, StringVar, BooleanVar, END, BOTH, LEFT, RIGHT, X, Y, filedialog, messagebox
from tkinter import ttk

APP_NAME = "Cosmetic-to-3D Creator"
HOME = Path.home() / "CosmeticTo3DProjects"
HOME.mkdir(parents=True, exist_ok=True)
CONFIG = Path.home() / ".cosmetic_to_3d_config.json"
SOURCES = {
    "Google Web":"https://www.google.com/search?q={q}", "Google Images":"https://www.google.com/search?tbm=isch&q={q}",
    "YouTube":"https://www.youtube.com/results?search_query={q}", "TikTok":"https://www.tiktok.com/search?q={q}",
    "Instagram (public web)":"https://www.google.com/search?q=site%3Ainstagram.com+{q}", "Facebook (public web)":"https://www.google.com/search?q=site%3Afacebook.com+{q}",
    "X / Twitter":"https://x.com/search?q={q}", "Reddit":"https://www.reddit.com/search/?q={q}",
    "Threads (public web)":"https://www.google.com/search?q=site%3Athreads.net+{q}", "Pinterest":"https://www.pinterest.com/search/pins/?q={q}",
    "Twitch (public web)":"https://www.google.com/search?q=site%3Atwitch.tv+{q}", "Discord public pages":"https://www.google.com/search?q=site%3Adiscord.com+{q}",
    "Sketchfab":"https://sketchfab.com/search?type=models&q={q}", "Cults3D":"https://cults3d.com/en/search?q={q}",
    "GitHub":"https://github.com/search?q={q}&type=repositories", "General forums":"https://www.google.com/search?q={q}+forum"
}
def enc(s): return urllib.parse.quote_plus(s.strip())
def read_config():
    try: return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception: return {}
def write_config(c): CONFIG.write_text(json.dumps(c, indent=2), encoding="utf-8")
def request_json(url, method="GET", headers=None, data=None, timeout=40):
    req=Request(url, data=data, headers=headers or {}, method=method)
    with urlopen(req, timeout=timeout) as r: return json.loads(r.read().decode("utf-8","replace"))
def public_search(query, limit=20):
    url="https://html.duckduckgo.com/html/?q="+urllib.parse.quote_plus(query)
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"})
    with urlopen(req,timeout=15) as r: page=r.read().decode("utf-8","replace")
    blocks=re.findall(r'<div class="result[^"]*".*?</div>\s*</div>',page,flags=re.I|re.S); out=[]
    for b in blocks:
        m=re.search(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',b,flags=re.I|re.S)
        if not m: continue
        u=html.unescape(m.group(1)); title=html.unescape(re.sub(r"\s+"," ",re.sub(r"<.*?>","",m.group(2)))).strip()
        sm=re.search(r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>',b,flags=re.I|re.S)
        snippet=html.unescape(re.sub(r"\s+"," ",re.sub(r"<.*?>","",sm.group(1)))).strip() if sm else ""
        if title and u.startswith("http"): out.append({"title":title,"url":u,"source":urllib.parse.urlparse(u).netloc.replace("www.",""),"snippet":snippet,"status":"Possible — verify manually"})
        if len(out)>=limit: break
    return out

class App(Tk):
    def __init__(self):
        super().__init__(); self.title(APP_NAME); self.geometry("1160x880"); self.minsize(900,700)
        self.cfg=read_config(); self.project=None; self.results=[]; self.images=[]; self.source_vars={}
        self._ui()
    def _ui(self):
        root=ttk.Frame(self,padding=12);root.pack(fill=BOTH,expand=True)
        ttk.Label(root,text=APP_NAME,font=("Segoe UI",18,"bold")).pack(anchor="w")
        ttk.Label(root,text="Search references, generate a 3D model through Meshy (API key required), then open/export with Blender.",foreground="#875600",wraplength=1100).pack(anchor="w",pady=(2,8))
        f=ttk.LabelFrame(root,text="Cosmetic details",padding=8);f.pack(fill=X)
        self.cosmetic=StringVar(value="Russian hat");self.creator=StringVar(value="TheMoobx");self.context=StringVar(value="Gorilla Tag");self.extra=StringVar(value="")
        for i,(label,var) in enumerate([("Cosmetic",self.cosmetic),("Creator username",self.creator),("Game / context",self.context),("Extra clues",self.extra)]):
            ttk.Label(f,text=label).grid(row=i,column=0,sticky="w",pady=3);ttk.Entry(f,textvariable=var).grid(row=i,column=1,sticky="ew",padx=8,pady=3)
            if i==1: ttk.Button(f,text="Copy username",command=self.copy_username).grid(row=i,column=2)
        f.columnconfigure(1,weight=1)
        nb=ttk.Notebook(root);nb.pack(fill=BOTH,expand=True,pady=8)
        self.search_tab=ttk.Frame(nb,padding=8);self.gen_tab=ttk.Frame(nb,padding=8);self.settings_tab=ttk.Frame(nb,padding=8)
        nb.add(self.search_tab,text="1. Search & references");nb.add(self.gen_tab,text="2. Generate / export 3D");nb.add(self.settings_tab,text="3. Settings")
        self._search_ui();self._gen_ui();self._settings_ui()
        self.status=StringVar(value="Ready.")
        ttk.Label(root,textvariable=self.status,wraplength=1100).pack(anchor="w")
        ttk.Label(root,text="Limitations: public searches may be incomplete; AI models are approximations. Social APIs/private content are not bypassed. API use may cost credits.",foreground="#555",wraplength=1100).pack(anchor="w",pady=(4,0))
    def _search_ui(self):
        box=ttk.LabelFrame(self.search_tab,text="Public source searches",padding=7);box.pack(fill=X)
        row=ttk.Frame(box);row.pack(fill=X)
        ttk.Button(row,text="Collect web results",command=self.collect).pack(side=LEFT)
        ttk.Button(row,text="Open selected searches",command=self.open_searches).pack(side=LEFT,padx=6)
        ttk.Button(row,text="Select all",command=lambda:self.select_sources(True)).pack(side=LEFT,padx=6)
        ttk.Button(row,text="Select none",command=lambda:self.select_sources(False)).pack(side=LEFT)
        grid=ttk.Frame(box);grid.pack(fill=X,pady=4)
        for i,name in enumerate(SOURCES):
            v=BooleanVar(value=True);self.source_vars[name]=v;ttk.Checkbutton(grid,text=name,variable=v).grid(row=i//4,column=i%4,sticky="w",padx=3,pady=2)
        for c in range(4):grid.columnconfigure(c,weight=1)
        results=ttk.LabelFrame(self.search_tab,text="Possible leads — verify manually",padding=6);results.pack(fill=BOTH,expand=True,pady=6)
        self.tree=ttk.Treeview(results,columns=("title","source","status"),show="headings",height=9)
        for col,title,width in [("title","Result",600),("source","Website",180),("status","Confidence",200)]:self.tree.heading(col,text=title);self.tree.column(col,width=width)
        self.tree.pack(side=LEFT,fill=BOTH,expand=True);sc=ttk.Scrollbar(results,orient="vertical",command=self.tree.yview);sc.pack(side=RIGHT,fill=Y);self.tree.configure(yscrollcommand=sc.set)
        actions=ttk.Frame(self.search_tab);actions.pack(fill=X)
        for label,cmd in [("Open result",self.open_result),("Copy URL",self.copy_url),("Export CSV",self.export_csv),("Create project",self.create_project),("Add reference images",self.add_images),("Save manifest",self.save_manifest)]:
            ttk.Button(actions,text=label,command=cmd).pack(side=LEFT,padx=3)
        ttk.Label(self.search_tab,text="Reference images are copied into the project folder; choose a clear single view for the image-to-3D request. Multiple views can improve identification, but this API call uses one selected image.",wraplength=1060).pack(anchor="w",pady=5)
    def _gen_ui(self):
        ttk.Label(self.gen_tab,text="Image-to-3D generation (Meshy API)",font=("Segoe UI",12,"bold")).pack(anchor="w")
        ttk.Label(self.gen_tab,text="Select a reference image and start an image-to-3D task. The app polls task status and downloads GLB/FBX outputs when available. A Meshy API key and credits may be required.",wraplength=1060).pack(anchor="w",pady=5)
        form=ttk.LabelFrame(self.gen_tab,text="Generation",padding=9);form.pack(fill=X)
        self.gen_image=StringVar(value="")
        ttk.Label(form,text="Input image").grid(row=0,column=0,sticky="w")
        ttk.Entry(form,textvariable=self.gen_image).grid(row=0,column=1,sticky="ew",padx=8)
        ttk.Button(form,text="Choose image",command=self.choose_gen_image).grid(row=0,column=2)
        self.model_type=StringVar(value="standard")
        ttk.Label(form,text="Model quality").grid(row=1,column=0,sticky="w",pady=5)
        ttk.Combobox(form,textvariable=self.model_type,values=["standard","smart-topology"],state="readonly",width=20).grid(row=1,column=1,sticky="w",padx=8,pady=5)
        self.texture=BooleanVar(value=True);ttk.Checkbutton(form,text="Generate textures",variable=self.texture).grid(row=2,column=1,sticky="w",padx=8)
        form.columnconfigure(1,weight=1)
        ttk.Button(form,text="Generate 3D model",command=self.generate_model).grid(row=3,column=1,sticky="w",padx=8,pady=8)
        self.generated_status=StringVar(value="No model generated yet.")
        ttk.Label(self.gen_tab,textvariable=self.generated_status,wraplength=1060).pack(anchor="w",pady=8)
        ttk.Label(self.gen_tab,text="Generated files",font=("Segoe UI",11,"bold")).pack(anchor="w")
        self.models=ttk.Treeview(self.gen_tab,columns=("file","format"),show="headings",height=10)
        self.models.heading("file",text="File");self.models.heading("format",text="Format");self.models.column("file",width=750);self.models.column("format",width=150)
        self.models.pack(fill=BOTH,expand=True,pady=5)
        row=ttk.Frame(self.gen_tab);row.pack(fill=X)
        ttk.Button(row,text="Open selected file",command=self.open_model).pack(side=LEFT)
        ttk.Button(row,text="Open generated folder",command=self.open_generated_folder).pack(side=LEFT,padx=6)
        ttk.Button(row,text="Convert to FBX + BLEND using Blender",command=self.blender_convert).pack(side=LEFT,padx=6)
    def _settings_ui(self):
        ttk.Label(self.settings_tab,text="Meshy API settings",font=("Segoe UI",12,"bold")).pack(anchor="w")
        ttk.Label(self.settings_tab,text="Create/manage a Meshy API key through its official developer platform. Keep it private. The key is stored locally in your Windows user profile.",wraplength=1060).pack(anchor="w",pady=5)
        self.api_key=StringVar(value=self.cfg.get("meshy_api_key",""))
        ttk.Label(self.settings_tab,text="Meshy API key").pack(anchor="w")
        ttk.Entry(self.settings_tab,textvariable=self.api_key,show="*",width=80).pack(fill=X,pady=4)
        self.blender_path=StringVar(value=self.cfg.get("blender_path",self.find_blender()))
        ttk.Label(self.settings_tab,text="Blender executable path (optional; auto-detected if installed)").pack(anchor="w",pady=(10,0))
        r=ttk.Frame(self.settings_tab);r.pack(fill=X,pady=4)
        ttk.Entry(r,textvariable=self.blender_path).pack(side=LEFT,fill=X,expand=True)
        ttk.Button(r,text="Browse",command=self.choose_blender).pack(side=LEFT,padx=6)
        ttk.Button(self.settings_tab,text="Save settings",command=self.save_settings).pack(anchor="w",pady=8)
        ttk.Label(self.settings_tab,text="Meshy API documentation: https://docs.meshy.ai/en/api/image-to-3d",foreground="#555").pack(anchor="w")
    def query(self):
        return " ".join(x.strip() for x in [self.cosmetic.get(),self.creator.get(),self.context.get(),self.extra.get()] if x.strip())
    def copy_username(self):
        s=self.creator.get().strip()
        if s:self.clipboard_clear();self.clipboard_append(s);self.update();self.status.set("Copied username.")
    def select_sources(self,v):
        for x in self.source_vars.values():x.set(v)
    def open_searches(self):
        q=self.query()
        if not q:return
        chosen=[n for n,v in self.source_vars.items() if v.get()]
        for n in chosen:webbrowser.open_new_tab(SOURCES[n].format(q=enc(q)))
        self.status.set(f"Opened {len(chosen)} searches.")
    def collect(self):
        q=self.query()
        if not q:return
        self.status.set("Attempting public web search…")
        threading.Thread(target=self._collect_worker,args=(q,),daemon=True).start()
    def _collect_worker(self,q):
        try:r=public_search(q);err=""
        except Exception as e:r=[];err=str(e)
        self.after(0,lambda:self.show_results(r,err))
    def show_results(self,r,err):
        for x in self.tree.get_children():self.tree.delete(x)
        self.results=r
        for d in r:self.tree.insert("",END,values=(d["title"],d["source"],d["status"]))
        self.status.set(f"Collected {len(r)} possible leads." if r else "No results parsed"+(": "+err[:120] if err else ". Open selected searches instead."))
        self.save_manifest(silent=True)
    def selected_result(self):
        s=self.tree.selection()
        return self.tree.index(s[0]) if s else None
    def open_result(self):
        i=self.selected_result()
        if i is not None:webbrowser.open_new_tab(self.results[i]["url"])
    def copy_url(self):
        i=self.selected_result()
        if i is not None:self.clipboard_clear();self.clipboard_append(self.results[i]["url"]);self.update()
    def export_csv(self):
        if not self.results:return
        p=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if p:
            with open(p,"w",newline="",encoding="utf-8-sig") as f:
                w=csv.DictWriter(f,fieldnames=["title","source","url","snippet","status"]);w.writeheader();w.writerows(self.results)
    def create_project(self):
        slug=re.sub(r"[^A-Za-z0-9_-]+","_",self.cosmetic.get().strip()).strip("_")[:50] or "cosmetic"
        p=HOME/slug;n=2
        while p.exists():p=HOME/f"{slug}_{n}";n+=1
        (p/"references").mkdir(parents=True);(p/"generated").mkdir()
        self.project=p;self.images=[];self.refresh_models();self.save_manifest();self.status.set(f"Project created at {p}")
    def add_images(self):
        if not self.project:messagebox.showinfo("Project","Create a project first.");return
        for src in filedialog.askopenfilenames(filetypes=[("Images","*.png *.jpg *.jpeg *.webp *.bmp")]):
            s=Path(src);d=self.project/"references"/s.name;i=2
            while d.exists():d=d.with_name(f"{s.stem}_{i}{s.suffix}");i+=1
            shutil.copy2(s,d);self.images.append(str(d))
        self.save_manifest()
        if self.images and not self.gen_image.get():self.gen_image.set(self.images[0])
        self.status.set(f"Added {len(self.images)} image(s).")
    def save_manifest(self,silent=False):
        if not self.project:return
        data={"cosmetic":self.cosmetic.get(),"creator_username":self.creator.get(),"context":self.context.get(),"results":self.results,"reference_images":[Path(p).name for p in self.images],"match_status":"POSSIBLE / UNVERIFIED until appearance and attribution are checked"}
        try:(self.project/"reference_manifest.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
        except Exception as e:
            if not silent:messagebox.showerror("Manifest",str(e))
    def choose_gen_image(self):
        p=filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg *.webp")])
        if p:self.gen_image.set(p)
    def save_settings(self):
        self.cfg={"meshy_api_key":self.api_key.get().strip(),"blender_path":self.blender_path.get().strip()}
        write_config(self.cfg);self.status.set("Settings saved locally.")
    def generate_model(self):
        key=self.api_key.get().strip()
        img=self.gen_image.get().strip()
        if not key:messagebox.showwarning("API key required","Add your Meshy API key in Settings. API access may require a paid plan or credits.");return
        if not img or not Path(img).is_file():messagebox.showwarning("Image required","Choose a local image file first.");return
        if not self.project:self.create_project()
        self.save_settings()
        self.generated_status.set("Uploading image and creating AI task…")
        threading.Thread(target=self._generate_worker,args=(img,key,self.model_type.get(),self.texture.get()),daemon=True).start()
    def _generate_worker(self,img,key,model_type,texture):
        try:
            size=Path(img).stat().st_size
            if size>20*1024*1024:raise ValueError("Image is over 20 MB. Choose a smaller image.")
            mime=mimetypes.guess_type(img)[0] or "image/png"
            with open(img,"rb") as f:uri="data:"+mime+";base64,"+base64.b64encode(f.read()).decode("ascii")
            body={"image_url":uri,"should_texture":bool(texture),"target_formats":["glb","fbx","obj"]}
            if model_type=="smart-topology":body.update({"model_type":"smart-topology","ai_model":"meshy-t2","target_polycount":10000})
            else:body.update({"model_type":"standard","ai_model":"meshy-7.1"})
            headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"}
            created=request_json("https://api.meshy.ai/openapi/v1/image-to-3d","POST",headers,json.dumps(body).encode("utf-8"),timeout=90)
            task_id=created.get("result")
            if not task_id:raise RuntimeError("API did not return a task ID: "+str(created)[:500])
            self.after(0,lambda:self.generated_status.set("Task created: "+task_id+" — waiting for generation…"))
            deadline=time.time()+1800
            task={}
            while time.time()<deadline:
                time.sleep(8)
                task=request_json("https://api.meshy.ai/openapi/v1/image-to-3d/"+task_id,headers=headers,timeout=60)
                status=task.get("status","UNKNOWN");progress=task.get("progress",0)
                self.after(0,lambda st=status,pr=progress:self.generated_status.set(f"AI generation status: {st} ({pr}%)"))
                if status in ("SUCCEEDED","FAILED","CANCELED"):break
            else:raise TimeoutError("Generation did not finish within 30 minutes. You can check the task in your Meshy account.")
            if task.get("status")!="SUCCEEDED":raise RuntimeError("AI task did not succeed: "+str(task.get("task_error",task))[:700])
            urls=task.get("model_urls",{})
            if not urls:raise RuntimeError("Task succeeded but returned no model URLs.")
            folder=self.project/"generated";folder.mkdir(exist_ok=True)
            for fmt,url in urls.items():
                if not url:continue
                out=folder/("model."+fmt)
                req=Request(url,headers={"User-Agent":"Mozilla/5.0"})
                with urlopen(req,timeout=120) as resp:out.write_bytes(resp.read())
            self.after(0,self.refresh_models)
            self.after(0,lambda:self.generated_status.set("Model downloaded. Select a file to open or convert with Blender. AI geometry is an approximation; inspect it."))
            self.after(0,lambda:self.status.set("3D model generation finished."))
        except Exception as e:
            msg=str(e)
            self.after(0,lambda m=msg:self.generated_status.set("Generation failed: "+m[:500]))
            self.after(0,lambda m=msg:messagebox.showerror("Generation failed",m[:1200]))
    def refresh_models(self):
        for x in self.models.get_children():self.models.delete(x)
        if not self.project:return
        for p in sorted((self.project/"generated").glob("*")):
            if p.is_file() and not p.name.startswith("_"):self.models.insert("",END,values=(p.name,p.suffix.lower()))
    def open_model(self):
        s=self.models.selection()
        if not s or not self.project:return
        p=self.project/"generated"/self.models.item(s[0],"values")[0]
        if p.exists():
            if sys.platform=="win32":os.startfile(p)
            else:webbrowser.open(p.as_uri())
    def open_generated_folder(self):
        if not self.project:messagebox.showinfo("Project","Create a project first.");return
        p=self.project/"generated"
        if sys.platform=="win32":os.startfile(p)
        else:webbrowser.open(p.as_uri())
    def find_blender(self):
        if os.environ.get("BLENDER_EXE") and Path(os.environ["BLENDER_EXE"]).exists():return os.environ["BLENDER_EXE"]
        for p in [r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"]:
            if Path(p).exists():return p
        import shutil as sh
        return sh.which("blender") or ""
    def choose_blender(self):
        p=filedialog.askopenfilename(filetypes=[("Blender executable","blender.exe"),("All files","*.*")])
        if p:self.blender_path.set(p)
    def blender_convert(self):
        if not self.project:messagebox.showinfo("Project","Create a project first.");return
        s=self.models.selection()
        if not s:messagebox.showinfo("Model","Select a model file first.");return
        src=self.project/"generated"/self.models.item(s[0],"values")[0]
        blender=self.blender_path.get().strip() or self.find_blender()
        if not blender or not Path(blender).exists():messagebox.showerror("Blender missing","Install Blender or set blender.exe in Settings.");return
        script=self.project/"generated"/"_export_with_blender.py"
        script.write_text('''import bpy,sys,os\nargs=sys.argv[sys.argv.index("--")+1:]\nsrc,outdir=args[0],args[1]\nstem=os.path.splitext(os.path.basename(src))[0]\nbpy.ops.wm.read_factory_settings(use_empty=True)\next=os.path.splitext(src)[1].lower()\nif ext==".obj": bpy.ops.wm.obj_import(filepath=src)\nelif ext==".stl": bpy.ops.wm.stl_import(filepath=src)\nelif ext==".ply": bpy.ops.wm.ply_import(filepath=src)\nelif ext in (".glb",".gltf"): bpy.ops.import_scene.gltf(filepath=src)\nelif ext==".fbx": bpy.ops.import_scene.fbx(filepath=src)\nelse: raise RuntimeError("Unsupported input format "+ext)\nbpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir,stem+".blend"))\nbpy.ops.export_scene.fbx(filepath=os.path.join(outdir,stem+".fbx"),use_selection=False)\n''',encoding="utf-8")
        self.status.set("Running Blender export…")
        threading.Thread(target=self._blender_worker,args=(blender,script,src),daemon=True).start()
    def _blender_worker(self,blender,script,src):
        try:
            p=subprocess.run([blender,"--background","--python",str(script),"--",str(src),str(src.parent)],capture_output=True,text=True,timeout=240)
            if p.returncode:raise RuntimeError((p.stderr or p.stdout)[-1500:])
            self.after(0,self.refresh_models);self.after(0,lambda:self.status.set("Blender exported .blend and .fbx."))
        except Exception as e:self.after(0,lambda m=str(e):messagebox.showerror("Blender export failed",m[:1500]))
    def close(self):
        self.save_settings();self.destroy()

if __name__=="__main__":
    app=App();app.protocol("WM_DELETE_WINDOW",app.close);app.mainloop()
