import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json, csv, os

class MelaminaSketch:
    def __init__(self, root):
        self.root=root; root.title("Diseño de Muebles Melamina - Estilo CAD v1.1")
        root.geometry("1360x820"); root.minsize(1050,650)
        self.parts=[]; self.selected=None
        self.v={k:tk.StringVar(value=x) for k,x in {
            "width":"800","height":"720","depth":"500","thick":"18","back":"9",
            "shelves":"2","divisions":"1","module":"Abierto","name":"Entrepaño"}.items()}
        self._ui(); self.refresh()

    def _ui(self):
        self.root.configure(bg="#d7dde4")
        menu=tk.Menu(self.root)
        for title, entries in [("Archivo",[("Nuevo",self.new),("Abrir proyecto",self.open),("Guardar proyecto",self.save),("Exportar despiece CSV",self.export),("Salir",self.root.destroy)]),
                               ("Ver",[("Vista 3D",self.draw),("Ajustar vista",self.draw)]),
                               ("Herramientas",[("Agregar entrepaño",lambda:self.add("Horizontal")),("Agregar división",lambda:self.add("Vertical"))]),
                               ("Ayuda",[("Acerca de",lambda:messagebox.showinfo("Acerca de","Prototipo de diseño paramétrico de muebles de melamina."))])]:
            m=tk.Menu(menu,tearoff=0)
            for label,cmd in entries: m.add_command(label=label,command=cmd)
            menu.add_cascade(label=title,menu=m)
        self.root.config(menu=menu)
        toolbar=tk.Frame(self.root,bg="#eef2f6",height=58,bd=1,relief="groove"); toolbar.pack(fill="x")
        tools=[("↖ Seleccionar",lambda:None),("▰ Módulo",self.add_module),("▱ Entrepaño",lambda:self.add("Horizontal")),
               ("▯ División",lambda:self.add("Vertical")),("◫ Puerta",lambda:self.add("Puerta")),
               ("⌗ Cantos",lambda:messagebox.showinfo("Cantos","Edición de cantos: función prevista para la siguiente versión.")),
               ("☷ Despiece",self.export),("💾 Guardar",self.save)]
        for label,cmd in tools:
            tk.Button(toolbar,text=label,command=cmd,bg="#f8fafc",activebackground="#dbeafe",
                      relief="flat",font=("Segoe UI",9),padx=10,pady=12).pack(side="left",padx=2,pady=3)
        body=tk.PanedWindow(self.root,orient="horizontal",sashwidth=5,bg="#b8c2cc"); body.pack(fill="both",expand=True)
        left=tk.Frame(body,bg="#f2f5f8",width=175); center=tk.Frame(body,bg="#dfe6ed"); right=tk.Frame(body,bg="#f2f5f8",width=285)
        body.add(left,minsize=140); body.add(center,minsize=470); body.add(right,minsize=250)
        tk.Label(left,text="VISTAS",bg="#e2e8f0",font=("Segoe UI",10,"bold"),anchor="w",padx=10,pady=8).pack(fill="x")
        for name in ["Vista 3D","Frontal","Superior","Lateral"]:
            tk.Button(left,text="▣  "+name,anchor="w",relief="flat",bg="#f8fafc",
                      command=self.draw).pack(fill="x",padx=8,pady=4)
        tk.Label(left,text="HERRAMIENTAS",bg="#e2e8f0",font=("Segoe UI",10,"bold"),anchor="w",padx=10,pady=8).pack(fill="x",pady=(14,0))
        for name,cmd in [("Seleccionar",lambda:None),("Agregar entrepaño",lambda:self.add("Horizontal")),
                         ("Agregar división",lambda:self.add("Vertical")),("Eliminar pieza",self.delete)]:
            tk.Button(left,text=name,anchor="w",relief="flat",bg="#f8fafc",command=cmd).pack(fill="x",padx=8,pady=3)
        tk.Label(center,text="MODELO 3D  |  Unidades: milímetros",anchor="w",bg="#f8fafc",font=("Segoe UI",10,"bold"),padx=10,pady=7).pack(fill="x")
        self.canvas=tk.Canvas(center,bg="#edf2f7",highlightthickness=0)
        self.canvas.pack(fill="both",expand=True)
        self.canvas.bind("<Configure>",lambda e:self.draw())
        self.canvas.bind("<Button-1>",self.pick)
        self.canvas.bind("<MouseWheel>",self.zoom)
        bottom=tk.Frame(center,bg="#f8fafc"); bottom.pack(fill="x")
        self.status=tk.Label(bottom,text="Listo | Selecciona una pieza o agrega un panel.",anchor="w",bg="#f8fafc",padx=8,pady=5)
        self.status.pack(fill="x")
        tk.Label(right,text="PROPIEDADES DEL MÓDULO",bg="#dbe4ed",font=("Segoe UI",10,"bold"),anchor="w",padx=10,pady=8).pack(fill="x")
        self._field(right,"Ancho exterior (mm)","width"); self._field(right,"Alto exterior (mm)","height")
        self._field(right,"Profundidad (mm)","depth"); self._field(right,"Espesor tablero (mm)","thick"); self._field(right,"Fondo (mm)","back")
        tk.Label(right,text="Configuración",bg="#e2e8f0",anchor="w",padx=8,pady=5).pack(fill="x",pady=(8,2))
        self._field(right,"Entrepaños","shelves"); self._field(right,"Divisiones verticales","divisions")
        row=tk.Frame(right,bg="#f2f5f8"); row.pack(fill="x",padx=8,pady=4)
        tk.Label(row,text="Tipo de módulo",bg="#f2f5f8").pack(anchor="w")
        ttk.Combobox(row,textvariable=self.v["module"],values=["Abierto","Con puertas","Cajonera"],state="readonly").pack(fill="x")
        tk.Button(right,text="Actualizar modelo",command=self.rebuild,bg="#cfe5ff",relief="flat",pady=7).pack(fill="x",padx=8,pady=8)
        tk.Label(right,text="LISTA DE PIEZAS",bg="#dbe4ed",font=("Segoe UI",10,"bold"),anchor="w",padx=10,pady=8).pack(fill="x",pady=(8,0))
        self.tree=ttk.Treeview(right,columns=("qty","l","w","t"),show="headings",height=11)
        for c,t,w in [("qty","Cant.",44),("l","Largo",62),("w","Ancho",62),("t","Esp.",48)]:
            self.tree.heading(c,text=t); self.tree.column(c,width=w,anchor="center")
        self.tree.pack(fill="both",expand=True,padx=6,pady=6)
        self.tree.bind("<<TreeviewSelect>>",self.select)
        self.root.bind("<Delete>",lambda e:self.delete())

    def _field(self,parent,label,key):
        f=tk.Frame(parent,bg="#f2f5f8"); f.pack(fill="x",padx=8,pady=3)
        tk.Label(f,text=label,bg="#f2f5f8",anchor="w").pack(fill="x")
        tk.Entry(f,textvariable=self.v[key],relief="solid",bd=1).pack(fill="x",ipady=3)

    def dims(self):
        try:
            d={k:float(self.v[k].get()) for k in ["width","height","depth","thick","back"]}
            if min(d["width"],d["height"],d["depth"],d["thick"])<=0 or d["back"]<0: raise ValueError
            return d
        except Exception:
            messagebox.showerror("Medidas","Introduce medidas numéricas válidas en milímetros."); return None

    def add_module(self):
        self.rebuild()
    def rebuild(self):
        d=self.dims()
        if not d:return
        self.parts=[]
        t=d["thick"]; W=d["width"]; H=d["height"]; D=d["depth"]
        self.parts += [
            {"name":"Lateral izquierdo","qty":1,"l":H,"w":D,"t":t,"axis":"Vertical","x":0,"z":0},
            {"name":"Lateral derecho","qty":1,"l":H,"w":D,"t":t,"axis":"Vertical","x":W-t,"z":0},
            {"name":"Tapa superior","qty":1,"l":W-2*t,"w":D,"t":t,"axis":"Horizontal","x":t,"z":H-t},
            {"name":"Base inferior","qty":1,"l":W-2*t,"w":D,"t":t,"axis":"Horizontal","x":t,"z":0},
        ]
        try: ns=max(0,min(12,int(self.v["shelves"].get()))); nd=max(0,min(8,int(self.v["divisions"].get())))
        except ValueError: ns=2; nd=1
        for i in range(ns):
            z=(H-2*t)*(i+1)/(ns+1)
            self.parts.append({"name":f"Entrepaño {i+1}","qty":1,"l":W-2*t,"w":D-d["back"],"t":t,"axis":"Horizontal","x":t,"z":z})
        for i in range(nd):
            x=(W-t)*(i+1)/(nd+1)
            self.parts.append({"name":f"División {i+1}","qty":1,"l":H-2*t,"w":D-d["back"],"t":t,"axis":"Vertical","x":x,"z":t})
        if d["back"]>0:
            self.parts.append({"name":"Fondo","qty":1,"l":H-2*t,"w":W-2*t,"t":d["back"],"axis":"Back","x":t,"z":t})
        self.selected=None; self.refresh(); self.status.config(text="Módulo actualizado. Verifica las medidas antes de fabricar.")

    def add(self,axis):
        d=self.dims()
        if not d:return
        t=d["thick"]
        if axis=="Vertical":
            p={"name":f"División {sum(x['axis']=='Vertical' for x in self.parts)}","qty":1,"l":d["height"]-2*t,"w":d["depth"]-d["back"],"t":t,"axis":axis,"x":d["width"]/2,"z":t}
        elif axis=="Puerta":
            p={"name":"Puerta","qty":1,"l":d["height"]-2*t,"w":d["width"]/2-t,"t":t,"axis":"Door","x":t,"z":t}
        else:
            p={"name":f"Entrepaño {sum(x['axis']=='Horizontal' for x in self.parts)}","qty":1,"l":d["width"]-2*t,"w":d["depth"]-d["back"],"t":t,"axis":"Horizontal","x":t,"z":d["height"]/2}
        self.parts.append(p); self.selected=len(self.parts)-1; self.refresh()
        self.status.config(text=f"Agregada: {p['name']}")

    def refresh(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for i,p in enumerate(self.parts):
            self.tree.insert("","end",iid=str(i),values=(p["qty"],round(p["l"]),round(p["w"]),round(p["t"])),text=p["name"])
        self.draw()

    def select(self,_=None):
        s=self.tree.selection()
        if s:self.selected=int(s[0]); self.status.config(text="Seleccionada: "+self.parts[self.selected]["name"]); self.draw()

    def pick(self,event):
        # Select nearest panel using approximate projected panel centers.
        if not self.parts:return
        self.selected=min(range(len(self.parts)),key=lambda i:abs(event.y-(self.canvas.winfo_height()*.55)))
        self.tree.selection_set(str(self.selected)); self.status.config(text="Seleccionada: "+self.parts[self.selected]["name"]); self.draw()

    def zoom(self,event):
        self.zoom_factor=getattr(self,"zoom_factor",1.0)*(1.1 if event.delta>0 else .9)
        self.zoom_factor=max(.5,min(2.5,self.zoom_factor)); self.draw()

    def draw(self):
        if not hasattr(self,"canvas"):return
        c=self.canvas;c.delete("all"); w=max(100,c.winfo_width()); h=max(100,c.winfo_height())
        try:d=self.dims_raw()
        except Exception:
            c.create_text(w/2,h/2,text="Introduce dimensiones válidas",fill="#a33");return
        W,H,D,T=[d[k] for k in ["width","height","depth","thick"]]
        scale=min(w*.48/(W+D*.45),h*.72/(H+D*.3))*getattr(self,"zoom_factor",1)
        ox=w*.27; oy=h*.80; ww=W*scale; hh=H*scale; dx=D*scale*.42; dy=D*scale*.23; t=T*scale
        A=(ox,oy-hh); B=(ox+ww,oy-hh); C=(ox+ww,oy); E=(ox,oy)
        A2=(A[0]+dx,A[1]-dy); B2=(B[0]+dx,B[1]-dy); C2=(C[0]+dx,C[1]-dy)
        # axis lines and floor grid
        for gx in range(0,w,40): c.create_line(gx,h*.88,gx,h,fill="#e2e8f0")
        for gy in range(int(h*.88),h,20): c.create_line(0,gy,w,gy,fill="#e2e8f0")
        c.create_polygon(A,B,B2,A2,fill="#d8c3a0",outline="#5b5144",width=2)
        c.create_polygon(B,C,C2,B2,fill="#c5b08f",outline="#5b5144",width=2)
        c.create_polygon(A,B,C,E,fill="#f7f7f4",outline="#475569",width=2)
        # interior opening
        c.create_polygon((ox+t,oy-hh+t),(ox+ww-t,oy-hh+t),(ox+ww-t,oy-t),(ox+t,oy-t),
                         fill="#e9edf1",outline="#64748b")
        for i,p in enumerate(self.parts):
            col="#1683d8" if i==self.selected else "#c5a77b"
            if p["axis"]=="Horizontal":
                yy=oy-p["z"]*scale
                c.create_polygon((ox+t,yy),(ox+ww-t,yy),(ox+ww-t+dx*.7,yy-dy*.7),(ox+t+dx*.7,yy-dy*.7),fill=col,outline="#51483d",width=1)
            elif p["axis"]=="Vertical":
                xx=ox+p["x"]*scale
                c.create_polygon((xx,oy-hh+t),(xx+dx*.6,oy-hh+t-dy*.6),(xx+dx*.6,oy-t-dy*.6),(xx,oy-t),fill=col,outline="#51483d",width=1)
        c.create_text(ox+ww/2,oy+25,text=f"{W:g} mm",fill="#1e293b",font=("Segoe UI",10,"bold"))
        c.create_text(ox-25,oy-hh/2,text=f"{H:g} mm",angle=90,fill="#1e293b")
        c.create_text(ox+ww+dx/2,oy-hh/2-dy/2,text=f"{D:g} mm",fill="#1e293b")
        c.create_text(w-115,20,text="MELAMINA PARAMÉTRICA",fill="#475569",font=("Segoe UI",10,"bold"))
        c.create_text(15,20,text="Ejes X / Y / Z  •  rueda = zoom",anchor="w",fill="#64748b")

    def dims_raw(self): return {k:float(self.v[k].get()) for k in ["width","height","depth","thick","back"]}

    def delete(self):
        if self.selected is not None and 0<=self.selected<len(self.parts):
            self.parts.pop(self.selected);self.selected=None;self.refresh();self.status.config(text="Pieza eliminada.")

    def new(self):
        self.parts=[];self.selected=None
        for k,x in {"width":"800","height":"720","depth":"500","thick":"18","back":"9","shelves":"2","divisions":"1","module":"Abierto","name":"Entrepaño"}.items():self.v[k].set(x)
        self.refresh();self.status.config(text="Proyecto nuevo.")

    def save(self):
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("Proyecto","*.json")])
        if not path:return
        try:
            with open(path,"w",encoding="utf-8") as f:json.dump({"dimensions":{k:self.v[k].get() for k in self.v},"parts":self.parts},f,ensure_ascii=False,indent=2)
            self.status.config(text="Proyecto guardado: "+path)
        except Exception as e:messagebox.showerror("Guardar",str(e))

    def open(self):
        path=filedialog.askopenfilename(filetypes=[("Proyecto","*.json")])
        if not path:return
        try:
            with open(path,encoding="utf-8") as f:d=json.load(f)
            for k,val in d["dimensions"].items():
                if k in self.v:self.v[k].set(str(val))
            self.parts=d["parts"];self.selected=None;self.refresh();self.status.config(text="Proyecto abierto.")
        except Exception as e:messagebox.showerror("Abrir",str(e))

    def export(self):
        if not self.parts:messagebox.showinfo("Despiece","Primero crea o agrega piezas.");return
        path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if not path:return
        try:
            with open(path,"w",newline="",encoding="utf-8-sig") as f:
                wr=csv.writer(f,delimiter=";");wr.writerow(["Nombre","Cantidad","Largo_mm","Ancho_mm","Espesor_mm","Tipo"])
                for p in self.parts:wr.writerow([p["name"],p["qty"],p["l"],p["w"],p["t"],p["axis"]])
            self.status.config(text="Despiece exportado: "+path)
        except Exception as e:messagebox.showerror("Exportar",str(e))

if __name__=="__main__":
    root=tk.Tk();app=MelaminaSketch(root);root.mainloop()
