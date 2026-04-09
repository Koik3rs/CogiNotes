
import tkinter as tk
from tkinter import filedialog, messagebox
import json, os, shutil, subprocess, sys, datetime
import sqlite3

#  DATABASE SETU
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_FILE     = os.path.join(BASE_DIR, "student_portal.db")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Import database module (located in parent directory)
import sys
sys.path.insert(0, os.path.dirname(BASE_DIR))
from database import db

ALLOWED_EXT = (".pdf", ".doc", ".docx", ".jpeg", ".jpg", ".png")
TYPE_COLORS = {
    "PDF":  "#e74c3c", "DOC": "#2980b9", 
    "JPEG": "#27ae60", "JPG": "#27ae60",
    "PNG":  "#8e44ad", "DOCX": "#2980b9",
}

# ── credentials (use database) ───────────────────────────────────
def load_credentials():
    """Load credentials from database."""
    return db.get_credentials()

# ── file metadata (use database) ─────────────────────────────────
def load_uploaded_files():
    """Load uploaded files metadata from database (only approved)."""
    meta = db.get_all_file_metadata()
    files = []
    for fname in sorted(os.listdir(UPLOADS_DIR)):
        fpath = os.path.join(UPLOADS_DIR, fname)
        if os.path.isfile(fpath):
            ext  = os.path.splitext(fname)[1].lower().lstrip(".")
            info = meta.get(fname, {})
            # Only show approved files to regular users
            if info.get("status") == "approved" or not info:
                files.append({
                    "name":    fname,
                    "type":    ext.upper(),
                    "path":    fpath,
                    "course":  info.get("course", ""),
                    "topic":   info.get("topic", ""),
                    "program": info.get("program", ""),
                    "uploader": info.get("uploader", ""),
                    "date":    info.get("date", ""),
                })
    return files

def save_file_metadata(filename, course="", topic="", program="", uploader=""):
    """Save file metadata to database."""
    db.save_file_metadata(filename, course, topic, program, uploader)

# ── forum (use database) ──────────────────────────────────────────
def load_forum():
    """Load forum posts from database."""
    return db.get_all_forum_posts()

def save_forum(posts):
    """This function is kept for compatibility but database handles this now."""
    pass  # Database already handles writes during post creation

def add_forum_post(author, title, body):
    """Add a forum post to database."""
    return db.add_forum_post(author, title, body)

def add_forum_reply(post_id, author, body):
    """Add a reply to a forum post in database."""
    return db.add_forum_reply(post_id, author, body)

# ══════════════════════════════════════════════════════════════════
#  WIDGET HELPERS
# ══════════════════════════════════════════════════════════════════
BG  = "#ffe5b7"
WH  = "white"
ACC = "#967240"
BORDER = "#cccccc"

def rounded_rect(canvas, x1, y1, x2, y2, radius=14, **kw):
    r = radius
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
           x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
           x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


class RF(tk.Canvas):          # RoundedFrame
    def __init__(self, parent, r=14, bg=WH, bc=BORDER, bw=1.5, **kw):
        pbg = parent["bg"] if hasattr(parent,"__getitem__") else parent.cget("bg")
        super().__init__(parent, bg=pbg, highlightthickness=0, **kw)
        self._r, self._bg, self._bc, self._bw = r, bg, bc, bw
        self.inner = tk.Frame(self, bg=bg)
        self._win  = self.create_window(0, 0, window=self.inner, anchor="nw")
        self.bind("<Configure>", self._resize)

    def _resize(self, e):
        w, h = e.width, e.height
        self.delete("_bg")
        rounded_rect(self, 1,1,w-1,h-1, radius=self._r,
                     fill=self._bg, outline=self._bc, width=self._bw, tags="_bg")
        p = self._r // 2
        self.coords(self._win, p, p)
        self.itemconfig(self._win, width=w-p*2, height=h-p*2)
        self.tag_lower("_bg")

    def configure(self, **kw):
        if "bg" in kw:
            self._bg = kw.pop("bg")
            self.inner.configure(bg=self._bg)
        super().configure(**kw)


class RB(tk.Canvas):          # RoundedButton
    def __init__(self, parent, text="", r=9, bg=WH, hbg="#e0e8f5",
                 fg="#222", bc=BORDER, font=("Helvetica",10),
                 cmd=None, **kw):
        pbg = parent["bg"] if hasattr(parent,"__getitem__") else parent.cget("bg")
        super().__init__(parent, bg=pbg, highlightthickness=0, **kw)
        self._t, self._r, self._bg, self._hbg = text, r, bg, hbg
        self._fg, self._bc, self._font, self._cmd = fg, bc, font, cmd
        self._cur = bg
        self.bind("<Configure>", self._draw)
        self.bind("<Enter>",     lambda e: self._col(hbg))
        self.bind("<Leave>",     lambda e: self._col(bg))
        self.bind("<Button-1>",  self._click)
        self.config(cursor="hand2")

    def _draw(self, _=None):
        self.delete("all")
        w = self.winfo_width()  or int(self["width"]  or 90)
        h = self.winfo_height() or int(self["height"] or 32)
        rounded_rect(self,1,1,w-1,h-1, radius=self._r,
                     fill=self._cur, outline=self._bc, width=1.5)
        self.create_text(w//2, h//2, text=self._t,
                         fill=self._fg, font=self._font)

    def _col(self, c):
        self._cur = c; self._draw()

    def _click(self, _):
        if self._cmd: self._cmd()

    def set_text(self, t):
        self._t = t; self._draw()


def avatar_canvas(parent, size=46, bg=WH):
    c = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0)
    s = size
    c.create_oval(3,3,s-3,s-3, fill="#d0d8e8", outline="#7a8fa6", width=2)
    c.create_oval(s//3, s//5, s*2//3, s*2//5, fill="#7a8fa6", outline="")
    c.create_arc(s//6, s//2, s*5//6, s, start=0, extent=180,
                 fill="#7a8fa6", outline="", style="chord")
    return c


def make_scrollable(parent, bg=WH):
    """Returns (outer_frame, inner_frame) with a vertical scrollbar."""
    outer = tk.Frame(parent, bg=bg)
    c = tk.Canvas(outer, bg=bg, highlightthickness=0)
    sb = tk.Scrollbar(outer, orient="vertical", command=c.yview)
    c.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    c.pack(side="left",  fill="both", expand=True)
    inner = tk.Frame(c, bg=bg)
    win   = c.create_window((0,0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: c.configure(scrollregion=c.bbox("all")))
    c.bind("<Configure>",     lambda e: c.itemconfig(win, width=e.width))
    # Mouse-wheel scroll
    def _scroll(e):
        c.yview_scroll(int(-1*(e.delta/120)), "units")
    c.bind_all("<MouseWheel>", _scroll)
    return outer, inner


# ══════════════════════════════════════════════════════════════════
#  APP CONTROLLER  (single-window navigation)
# ══════════════════════════════════════════════════════════════════
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Study Buddy: Student Hub")
        self.root.configure(bg=BG)
        self.username = ""
        self._current_preview_path = None   # file shown in main preview
        self._show_login()
        self.root.mainloop()

    # ── helpers ──────────────────────────────────────────────────
    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def _set_size(self, geo, resizable=True):
        self.root.geometry(geo)
        self.root.resizable(resizable, resizable)

    # ─────────────────────────────────────────────────────────────
    #  LOGIN
    # ─────────────────────────────────────────────────────────────
    def _show_login(self):
        self._clear()
        self._set_size("520x500", False)
        self.root.title("Student Portal – Login")
        self.root["bg"] = BG

        card = RF(self.root, r=20, bg=WH, bc=BORDER, bw=1.5)
        card.place(relx=.5, rely=.5, anchor="center", width=370, height=430)
        i = card.inner

        av = avatar_canvas(i, size=32)
        av.pack(pady=(28,0))

        tk.Label(i, text="Welcome Back", bg=WH, fg="#222",
                 font=("Helvetica",16,"bold")).pack(pady=(10,4))
        tk.Label(i, text="Student Portal", bg=WH, fg="#888",
                 font=("Helvetica",10)).pack(pady=(0,14))

        err_v = tk.StringVar()
        tk.Label(i, textvariable=err_v, bg=WH, fg="#c0392b",
                 font=("Helvetica",9)).pack()

        # ── student number ──
        sf = tk.Frame(i, bg=WH); sf.pack(fill="x", padx=32, pady=(4,8))
        sc = tk.Canvas(sf, bg=WH, highlightthickness=0, height=44)
        sc.pack(fill="x")
        se = tk.Entry(sc, font=("Helvetica",11), bg=WH, bd=0,
                      highlightthickness=0, fg="#aaa", insertbackground="#333")
        se.insert(0,"Student Number")

        def _sn_draw(e):
            sc.delete("all")
            rounded_rect(sc,1,1,e.width-1,e.height-1, fill=WH, outline="#bbb", width=1.5)
            sc.create_text(26,e.height//2, text="🪪", font=("Helvetica",13), anchor="center")
            sc.create_window(e.width//2+14, e.height//2, window=se,
                             width=e.width-62, height=e.height-14)
        sc.bind("<Configure>", _sn_draw)

        def _sn_in(_):
            if se.get()=="Student Number": se.delete(0,"end"); se.config(fg="#333")
        def _sn_out(_):
            if not se.get(): se.insert(0,"Student Number"); se.config(fg="#aaa")
        se.bind("<FocusIn>",_sn_in); se.bind("<FocusOut>",_sn_out)

        # ── password ──
        pf = tk.Frame(i, bg=WH); pf.pack(fill="x", padx=32, pady=(0,18))
        pc = tk.Canvas(pf, bg=WH, highlightthickness=0, height=44)
        pc.pack(fill="x")
        pe = tk.Entry(pc, font=("Helvetica",11), bg=WH, bd=0,
                      highlightthickness=0, fg="#aaa", insertbackground="#333")
        pe.insert(0,"Password")
        _vis = [False]

        def _toggle_pw():
            _vis[0] = not _vis[0]
            pe.config(show="" if _vis[0] else ("*" if pe.get()!="Password" else ""))
            eye.config(text="🙈" if _vis[0] else "👁")

        eye = tk.Button(pc, text="👁", bg=WH, bd=0, highlightthickness=0,
                        fg="#888", font=("Helvetica",12), cursor="hand2",
                        command=_toggle_pw)

        def _pw_draw(e):
            pc.delete("all")
            rounded_rect(pc,1,1,e.width-1,e.height-1, fill=WH, outline="#bbb", width=1.5)
            pc.create_text(26,e.height//2, text="🔒", font=("Helvetica",13), anchor="center")
            pc.create_window(e.width//2+6, e.height//2, window=pe,
                             width=e.width-82, height=e.height-14)
            pc.create_window(e.width-22, e.height//2, window=eye)
        pc.bind("<Configure>", _pw_draw)

        def _pw_in(_):
            if pe.get()=="Password": pe.delete(0,"end"); pe.config(fg="#333",show="*")
        def _pw_out(_):
            if not pe.get(): pe.insert(0,"Password"); pe.config(fg="#aaa",show="")
        pe.bind("<FocusIn>",_pw_in); pe.bind("<FocusOut>",_pw_out)

        # ── buttons ──
        br = tk.Frame(i, bg=WH); br.pack(fill="x", padx=32)

        def _do_login():
            sn = se.get().strip(); pw = pe.get().strip()
            if sn=="Student Number" or not sn:
                err_v.set("Enter your student number."); return
            if pw=="Password" or not pw:
                err_v.set("Enter your password."); return
            if db.verify_user(sn, pw):
                self.username = sn
                self._show_main()
            else:
                err_v.set("Invalid credentials. Try again.")

        RB(br, text="Cancel", r=8, width=130, height=38,
           cmd=self.root.destroy).pack(side="left", padx=(0,10))
        RB(br, text="Login",  r=8, width=130, height=38,
           bg="#5588cc", hbg="#3a6aaa", fg=WH, bc="#3a6aaa",
           cmd=_do_login).pack(side="left")

        self.root.bind("<Return>", lambda _: _do_login())

        tk.Label(i, text="Don't have access? Use your standard credentials",
                 bg=WH, fg="#aaa", font=("Helvetica",8)).pack(pady=(14,2))
        forgot = tk.Label(i, text="Forgot password?", bg=WH, fg=ACC,
                          font=("Helvetica",9,"underline"), cursor="hand2")
        forgot.pack()
        forgot.bind("<Button-1>", lambda _: messagebox.showinfo(
            "Password Reset","Contact your administrator to reset your password."))

        register = tk.Label(i, text="Create new account", bg=WH, fg=ACC,
                          font=("Helvetica",9,"underline"), cursor="hand2")
        register.pack(pady=(4,0))
        register.bind("<Button-1>", lambda _: self._show_register())

    # ─────────────────────────────────────────────────────────────
    #  REGISTER
    # ─────────────────────────────────────────────────────────────
    def _show_register(self):
        self._clear()
        self._set_size("520x500", False)
        self.root.title("Student Portal – Register")
        self.root["bg"] = BG

        card = RF(self.root, r=20, bg=WH, bc=BORDER, bw=1.5)
        card.place(relx=.5, rely=.5, anchor="center", width=370, height=480)
        i = card.inner

        av = avatar_canvas(i, size=32)
        av.pack(pady=(28,0))

        tk.Label(i, text="Create Account", bg=WH, fg="#222",
                 font=("Helvetica",16,"bold")).pack(pady=(10,4))
        tk.Label(i, text="Student Portal", bg=WH, fg="#888",
                 font=("Helvetica",10)).pack(pady=(0,14))

        err_v = tk.StringVar()
        tk.Label(i, textvariable=err_v, bg=WH, fg="#c0392b",
                 font=("Helvetica",9)).pack()

        # ── username ──
        uf = tk.Frame(i, bg=WH); uf.pack(fill="x", padx=32, pady=(4,8))
        uc = tk.Canvas(uf, bg=WH, highlightthickness=0, height=44)
        uc.pack(fill="x")
        ue = tk.Entry(uc, font=("Helvetica",11), bg=WH, bd=0,
                      highlightthickness=0, fg="#aaa", insertbackground="#333")
        ue.insert(0,"Username")

        def _un_draw(e):
            uc.delete("all")
            rounded_rect(uc,1,1,e.width-1,e.height-1, fill=WH, outline="#bbb", width=1.5)
            uc.create_text(26,e.height//2, text="👤", font=("Helvetica",13), anchor="center")
            uc.create_window(e.width//2+14, e.height//2, window=ue,
                             width=e.width-62, height=e.height-14)
        uc.bind("<Configure>", _un_draw)

        def _un_in(_):
            if ue.get()=="Username": ue.delete(0,"end"); ue.config(fg="#333")
        def _un_out(_):
            if not ue.get(): ue.insert(0,"Username"); ue.config(fg="#aaa")
        ue.bind("<FocusIn>",_un_in); ue.bind("<FocusOut>",_un_out)

        # ── password ──
        pf = tk.Frame(i, bg=WH); pf.pack(fill="x", padx=32, pady=(0,8))
        pc = tk.Canvas(pf, bg=WH, highlightthickness=0, height=44)
        pc.pack(fill="x")
        pe = tk.Entry(pc, font=("Helvetica",11), bg=WH, bd=0,
                      highlightthickness=0, fg="#aaa", insertbackground="#333")
        pe.insert(0,"Password")
        _vis = [False]

        def _toggle_pw():
            _vis[0] = not _vis[0]
            pe.config(show="" if _vis[0] else ("*" if pe.get()!="Password" else ""))
            eye.config(text="🙈" if _vis[0] else "👁")

        eye = tk.Button(pc, text="👁", bg=WH, bd=0, highlightthickness=0,
                        fg="#888", font=("Helvetica",12), cursor="hand2",
                        command=_toggle_pw)

        def _pw_draw(e):
            pc.delete("all")
            rounded_rect(pc,1,1,e.width-1,e.height-1, fill=WH, outline="#bbb", width=1.5)
            pc.create_text(26,e.height//2, text="🔒", font=("Helvetica",13), anchor="center")
            pc.create_window(e.width//2+6, e.height//2, window=pe,
                             width=e.width-82, height=e.height-14)
            pc.create_window(e.width-22, e.height//2, window=eye)
        pc.bind("<Configure>", _pw_draw)

        def _pw_in(_):
            if pe.get()=="Password": pe.delete(0,"end"); pe.config(fg="#333",show="*")
        def _pw_out(_):
            if not pe.get(): pe.insert(0,"Password"); pe.config(fg="#aaa",show="")
        pe.bind("<FocusIn>",_pw_in); pe.bind("<FocusOut>",_pw_out)

        # ── confirm password ──
        cf = tk.Frame(i, bg=WH); cf.pack(fill="x", padx=32, pady=(0,18))
        cc = tk.Canvas(cf, bg=WH, highlightthickness=0, height=44)
        cc.pack(fill="x")
        ce = tk.Entry(cc, font=("Helvetica",11), bg=WH, bd=0,
                      highlightthickness=0, fg="#aaa", insertbackground="#333")
        ce.insert(0,"Confirm Password")

        def _c_draw(e):
            cc.delete("all")
            rounded_rect(cc,1,1,e.width-1,e.height-1, fill=WH, outline="#bbb", width=1.5)
            cc.create_text(26,e.height//2, text="🔒", font=("Helvetica",13), anchor="center")
            cc.create_window(e.width//2+14, e.height//2, window=ce,
                             width=e.width-62, height=e.height-14)
        cc.bind("<Configure>", _c_draw)

        def _c_in(_):
            if ce.get()=="Confirm Password": ce.delete(0,"end"); ce.config(fg="#333",show="*")
        def _c_out(_):
            if not ce.get(): ce.insert(0,"Confirm Password"); ce.config(fg="#aaa",show="")
        ce.bind("<FocusIn>",_c_in); ce.bind("<FocusOut>",_c_out)

        # ── buttons ──
        br = tk.Frame(i, bg=WH); br.pack(fill="x", padx=32)

        def _do_register():
            un = ue.get().strip(); pw = pe.get().strip(); cp = ce.get().strip()
            if un=="Username" or not un:
                err_v.set("Enter a username."); return
            if pw=="Password" or not pw:
                err_v.set("Enter a password."); return
            if cp=="Confirm Password" or not cp:
                err_v.set("Confirm your password."); return
            if pw != cp:
                err_v.set("Passwords do not match."); return
            if len(pw) < 6:
                err_v.set("Password must be at least 6 characters."); return
            if db.add_user(un, pw):
                messagebox.showinfo("Success", "Account created successfully! You can now login.")
                self._show_login()
            else:
                err_v.set("Username already exists. Choose a different one.")

        RB(br, text="Back", r=8, width=130, height=38,
           cmd=self._show_login).pack(side="left", padx=(0,10))
        RB(br, text="Register",  r=8, width=130, height=38,
           bg="#27ae60", hbg="#229954", fg=WH, bc="#229954",
           cmd=_do_register).pack(side="left")

        self.root.bind("<Return>", lambda _: _do_register())

    # ─────────────────────────────────────────────────────────────
    #  SHARED SHELL  (header + sidebar reused across main screens)
    # ─────────────────────────────────────────────────────────────
    def _build_shell(self, title="Student Portal"):
        """Builds outer+header+body.  Returns (body_frame, sidebar_inner)."""
        self._clear()
        self._set_size("960x580")
        self.root.title(title)
        self.root["bg"] = BG

        outer = RF(self.root, r=18, bg=BG, bc="#bbb", bw=2)
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        # header
        hdr = RF(outer.inner, r=12, bg=WH, bc=BORDER, bw=1.5, height=66)
        hdr.pack(fill="x", padx=8, pady=(8,6))
        hdr.pack_propagate(False)

        pf = tk.Frame(hdr.inner, bg=WH)
        pf.pack(side="left", padx=14, pady=10)
        
        # Profile picture or avatar
        profile_pic = db.get_profile_picture(self.username)
        if profile_pic and os.path.exists(profile_pic):
            try:
                from PIL import Image, ImageTk
                img = Image.open(profile_pic)
                img.thumbnail((40, 40))
                photo = ImageTk.PhotoImage(img)
                pic_lbl = tk.Label(pf, image=photo, bg=WH)
                pic_lbl.image = photo
                pic_lbl.pack(side="left", padx=(0,8))
            except:
                avatar_canvas(pf).pack(side="left")
        else:
            avatar_canvas(pf).pack(side="left")
        
        tk.Label(pf, text=self.username, bg=WH, fg="#333",
                 font=("Helvetica",11,"bold")).pack(side="left", padx=(10,0))
        
        # Change picture button
        RB(pf, text="📷", r=8, width=32, height=24,
           font=("Helvetica",10),
           cmd=self._change_profile_picture).pack(side="left", padx=(8,0))

        # logout btn
        RB(hdr.inner, text="⏻  Logout", r=8, width=90, height=30,
           font=("Helvetica",9), cmd=self._logout,
           bc="#ddaaaa", hbg="#fdecea").pack(side="right", padx=14)

        # body row
        body = tk.Frame(outer.inner, bg=BG)
        body.pack(fill="both", expand=True, padx=8, pady=(0,8))

        # sidebar
        sb = RF(body, r=12, bg=WH, bc=BORDER, bw=1.5, width=175)
        sb.pack(side="left", fill="y", padx=(0,6))
        sb.pack_propagate(False)

        tk.Label(sb.inner, text="Navigation", bg=WH, fg="#aaa",
                 font=("Helvetica",8,"bold")).pack(pady=(14,6))

        nav_btns = {}
        nav_labels = ["Home","Browse","Forums","Downloads","Upload"]
        if self.username == "admin":
            nav_labels.append("Admin Panel")
        
        for label in nav_labels:
            b = RB(sb.inner, text=label, r=8, width=138, height=34,
                   font=("Helvetica",10))
            b.pack(pady=3)
            nav_btns[label] = b

        nav_btns["Home"]._cmd      = self._show_main
        nav_btns["Browse"]._cmd     = self._show_browse
        nav_btns["Forums"]._cmd     = self._show_forums
        nav_btns["Downloads"]._cmd  = self._show_downloads
        nav_btns["Upload"]._cmd     = self._show_upload
        if self.username == "admin":
            nav_btns["Admin Panel"]._cmd = self._show_admin_panel

        return body, nav_btns

    def _logout(self):
        self.username = ""
        self._show_login()

    def _change_profile_picture(self):
        """Allow user to change their profile picture."""
        fts = [("Image files","*.jpg *.jpeg *.png"),("All files","*.*")]
        path = filedialog.askopenfilename(title="Choose profile picture", filetypes=fts)
        if not path:
            return
        
        # Create profiles directory if needed
        profiles_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        
        # Save with username as filename
        ext = os.path.splitext(path)[1]
        pic_path = os.path.join(profiles_dir, f"{self.username}{ext}")
        
        try:
            # Resize image if needed
            from PIL import Image
            img = Image.open(path)
            img.thumbnail((200, 200))
            img.save(pic_path)
            
            # Update database
            db.set_profile_picture(self.username, pic_path)
            messagebox.showinfo("Success", "Profile picture updated!")
            
            # Refresh the current screen
            self._show_main()
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to update picture: {str(ex)}")

    # ─────────────────────────────────────────────────────────────
    #  MAIN / HOME
    # ─────────────────────────────────────────────────────────────
    def _show_main(self):
        body, nav = self._build_shell("Student Portal – Home")
        nav["Home"]._col(nav["Home"]._hbg)   # highlight active

        content = RF(body, r=12, bg=WH, bc=BORDER, bw=1.5)
        content.pack(side="left", fill="both", expand=True)

        # preview area
        prev_outer = RF(content.inner, r=10, bg="#fafafa", bc=BORDER, bw=1.5)
        prev_outer.pack(fill="both", expand=True, padx=10, pady=(10,8))

        self._preview_label = tk.Label(prev_outer.inner,
                                       text="Select a file to preview",
                                       bg="#fafafa", fg="#aaa",
                                       font=("Helvetica",11))
        self._preview_label.pack(expand=True)
        self._preview_inner = prev_outer.inner
        self._preview_image_ref = None   # keep reference

        # recent files list (quick-select for preview)
        files = load_uploaded_files()[-5:]   # last 5
        if files:
            bar = tk.Frame(content.inner, bg=WH)
            bar.pack(fill="x", padx=10, pady=(0,4))
            tk.Label(bar, text="Recent files:", bg=WH, fg="#888",
                     font=("Helvetica",8)).pack(side="left")
            for f in reversed(files):
                def _sel(fp=f["path"], fn=f["name"], ft=f["type"]):
                    self._show_file_preview(fp, fn, ft)
                RB(bar, text=f["name"][:22], r=6,
                   width=min(180, len(f["name"][:22])*8+20), height=24,
                   font=("Helvetica",8), cmd=_sel).pack(side="left", padx=3)

        # browse / upload buttons
        br = tk.Frame(content.inner, bg=WH)
        br.pack(anchor="w", padx=14, pady=(0,12))
        RB(br, text="Browse",  r=8, width=88, height=32, cmd=self._show_browse).pack(side="left", padx=(0,8))
        RB(br, text="Upload",  r=8, width=88, height=32, cmd=self._show_upload).pack(side="left")

    def _show_file_preview(self, path, name, ftype):
        """Update the preview panel in the main screen."""
        for w in self._preview_inner.winfo_children():
            w.destroy()
        self._preview_image_ref = None

        ext = os.path.splitext(name)[1].lower()

        # image preview
        if ext in (".png",".jpg",".jpeg"):
            try:
                from PIL import Image, ImageTk
                img = Image.open(path)
                img.thumbnail((460,260))
                photo = ImageTk.PhotoImage(img)
                self._preview_image_ref = photo
                lbl = tk.Label(self._preview_inner, image=photo, bg="#fafafa")
                lbl.pack(expand=True, pady=8)
                tk.Label(self._preview_inner, text=name, bg="#fafafa", fg="#555",
                         font=("Helvetica",9)).pack()
                return
            except ImportError:
                pass   # PIL not installed – fall through to text preview

        # CSV preview
        if ext == ".csv":
            try:
                import csv
                with open(path, newline="", encoding="utf-8", errors="replace") as f:
                    reader = csv.reader(f)
                    rows = [r for _,r in zip(range(8), reader)]
                frame = tk.Frame(self._preview_inner, bg="#fafafa")
                frame.pack(expand=True, fill="both", padx=8, pady=8)
                for ri, row in enumerate(rows):
                    for ci, cell in enumerate(row[:6]):
                        bg = "#e8f0fb" if ri==0 else "#fafafa"
                        tk.Label(frame, text=cell[:18], bg=bg, fg="#333",
                                 font=("Helvetica",8,"bold" if ri==0 else "normal"),
                                 relief="flat", bd=1, padx=4, pady=2,
                                 width=14, anchor="w").grid(row=ri, column=ci, sticky="nsew", padx=1, pady=1)
                tk.Label(self._preview_inner, text=name, bg="#fafafa", fg="#555",
                         font=("Helvetica",9)).pack()
                return
            except Exception:
                pass

        # generic / PDF / DOC – show icon + info
        color = TYPE_COLORS.get(ftype, "#7f8c8d")
        ic = tk.Canvas(self._preview_inner, width=72, height=72,
                       bg="#fafafa", highlightthickness=0)
        ic.pack(expand=True, pady=(30,4))
        ic.create_oval(4,4,68,68, fill=color, outline="")
        ic.create_text(36,36, text=ftype[:3], fill=WH,
                       font=("Helvetica",14,"bold"))
        tk.Label(self._preview_inner, text=name, bg="#fafafa", fg="#333",
                 font=("Helvetica",10,"bold")).pack()
        try:
            size = os.path.getsize(path)
            sz = f"{size/1024:.1f} KB" if size<1048576 else f"{size/1048576:.1f} MB"
        except: sz=""
        tk.Label(self._preview_inner, text=f"Type: {ftype}   Size: {sz}",
                 bg="#fafafa", fg="#888", font=("Helvetica",9)).pack(pady=(2,24))

    # ─────────────────────────────────────────────────────────────
    #  UPLOAD  (full screen with preview & confirm)
    # ─────────────────────────────────────────────────────────────
    def _show_upload(self):
        body, nav = self._build_shell("Student Portal – Upload")
        nav["Upload"]._col(nav["Upload"]._hbg)

        content = RF(body, r=12, bg=WH, bc=BORDER, bw=1.5)
        content.pack(side="left", fill="both", expand=True)

        # ── ALWAYS-VISIBLE TOP STRIP ─────────────────────────────
        top = tk.Frame(content.inner, bg=WH)
        top.pack(fill="x", padx=20, pady=(14, 6))

        # Row 1: title + buttons
        row1 = tk.Frame(top, bg=WH)
        row1.pack(fill="x", pady=(0, 6))
        tk.Label(row1, text="Upload a File", bg=WH, fg="#333",
                 font=("Helvetica",13,"bold")).pack(side="left")

        btn_row = tk.Frame(row1, bg=WH)
        btn_row.pack(side="right")

        choose_btn = RB(btn_row, text="📂  Choose File", r=8,
                        width=128, height=34, font=("Helvetica",10))
        choose_btn.pack(side="left", padx=(0, 6))

        confirm_btn = RB(btn_row, text="✔  Confirm Upload", r=8,
                         width=150, height=34, bg="#5588cc", hbg="#3a6aaa",
                         fg=WH, bc="#3a6aaa", font=("Helvetica",10,"bold"))
        confirm_btn.pack(side="left")
        confirm_btn._cmd = lambda: None   # set below

        # Row 2: allowed types hint
        tk.Label(top, text="Allowed types: PDF, DOC/DOCX, JPEG, PNG, CSV",
                 bg=WH, fg="#888", font=("Helvetica",9)).pack(anchor="w")

        # Row 3: selected-file banner
        dz = RF(top, r=10, bg="#f5f8ff", bc="#a0b8e0", bw=2, height=38)
        dz.pack(fill="x", pady=(6, 0))
        dz.pack_propagate(False)
        tk.Label(dz.inner, text='No file selected — click "Choose File" above',
                 bg="#f5f8ff", fg="#9ab0d0", font=("Helvetica",9)).pack(expand=True)

        # Row 4: metadata fields (horizontal)
        fields_frame = tk.Frame(top, bg=WH)
        fields_frame.pack(fill="x", pady=(8, 0))

        def lbl_entry(parent, label):
            f = tk.Frame(parent, bg=WH)
            f.pack(side="left", fill="x", expand=True, padx=(0, 10))
            tk.Label(f, text=label, bg=WH, fg="#555",
                     font=("Helvetica",8), anchor="w").pack(anchor="w")
            e = tk.Entry(f, font=("Helvetica",10), bg="#f9f9f9",
                         bd=1, relief="solid", highlightthickness=0)
            e.pack(fill="x", ipady=4)
            return e

        e_course  = lbl_entry(fields_frame, "Course Code:")
        e_topic   = lbl_entry(fields_frame, "Topic:")
        e_program = lbl_entry(fields_frame, "Program:")

        # ── PREVIEW PANEL (fills remaining vertical space) ───────
        pv = RF(content.inner, r=10, bg="#fafafa", bc=BORDER, bw=1.5)
        pv.pack(fill="both", expand=True, padx=20, pady=(10, 14))
        tk.Label(pv.inner, text="File preview will appear here",
                 bg="#fafafa", fg="#bbb", font=("Helvetica",10)).pack(expand=True)
        self._up_preview_inner = pv.inner
        self._up_img_ref = None
        self._selected_path = [None]
        self._selected_name = [None]

        def _choose():
            fts = [("Allowed files","*.pdf *.doc *.docx *.jpeg *.jpg *.png *.csv"),
                   ("PDF","*.pdf"),("Word","*.doc *.docx"),
                   ("Image","*.jpeg *.jpg *.png"),("CSV","*.csv")]
            path = filedialog.askopenfilename(title="Choose file", filetypes=fts)
            if not path: return
            ext = os.path.splitext(path)[1].lower()
            if ext not in ALLOWED_EXT:
                messagebox.showerror("Not allowed",
                    f"File type '{ext}' is not permitted."); return
            self._selected_path[0] = path
            name = os.path.basename(path)
            self._selected_name[0] = name
            # update drop-zone label
            for w in dz.inner.winfo_children(): w.destroy()
            tk.Label(dz.inner, text=f"✅  {name}",
                     bg="#f5f8ff", fg="#2e7d32",
                     font=("Helvetica",11,"bold")).pack(expand=True)
            # show preview
            _render_upload_preview(path, name, os.path.splitext(name)[1].lstrip(".").upper())

        def _render_upload_preview(path, name, ftype):
            for w in self._up_preview_inner.winfo_children(): w.destroy()
            self._up_img_ref = None
            ext = os.path.splitext(name)[1].lower()
            if ext in (".png",".jpg",".jpeg"):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(path); img.thumbnail((400,180))
                    photo = ImageTk.PhotoImage(img)
                    self._up_img_ref = photo
                    tk.Label(self._up_preview_inner, image=photo,
                             bg="#fafafa").pack(expand=True, pady=6)
                    tk.Label(self._up_preview_inner, text=name,
                             bg="#fafafa", fg="#555", font=("Helvetica",9)).pack()
                    return
                except ImportError: pass
            if ext == ".csv":
                try:
                    import csv
                    with open(path, newline="", encoding="utf-8", errors="replace") as f:
                        rows = [r for _,r in zip(range(5), csv.reader(f))]
                    fr = tk.Frame(self._up_preview_inner, bg="#fafafa")
                    fr.pack(expand=True, fill="both", padx=8, pady=8)
                    for ri,row in enumerate(rows):
                        for ci,cell in enumerate(row[:5]):
                            bg = "#e8f0fb" if ri==0 else "#fafafa"
                            tk.Label(fr, text=cell[:16], bg=bg, fg="#333",
                                     font=("Helvetica",8,"bold" if ri==0 else "normal"),
                                     relief="flat", bd=1, padx=3, pady=2,
                                     width=13, anchor="w").grid(row=ri,column=ci,
                                     sticky="nsew",padx=1,pady=1)
                    return
                except Exception: pass
            color = TYPE_COLORS.get(ftype,"#7f8c8d")
            ic = tk.Canvas(self._up_preview_inner, width=60, height=60,
                           bg="#fafafa", highlightthickness=0)
            ic.pack(expand=True, pady=(14,4))
            ic.create_oval(4,4,56,56, fill=color, outline="")
            ic.create_text(30,30, text=ftype[:3], fill=WH,
                           font=("Helvetica",12,"bold"))
            tk.Label(self._up_preview_inner, text=name,
                     bg="#fafafa", fg="#333", font=("Helvetica",9)).pack()

        def _confirm():
            path = self._selected_path[0]
            if not path:
                messagebox.showwarning("No file","Please choose a file first."); return
            name = self._selected_name[0]
            dest = os.path.join(UPLOADS_DIR, name)
            if os.path.exists(dest):
                if not messagebox.askyesno("Overwrite?",
                        f"{name} already exists.\nOverwrite?"): return
            shutil.copy2(path, dest)
            # save metadata to database with PENDING status
            db.save_file_metadata(name, e_course.get().strip(), e_topic.get().strip(),
                             e_program.get().strip(), self.username)
            messagebox.showinfo("Upload Pending", 
                f"'{name}' uploaded!\nIt will be visible once approved by an admin.")
            self._show_main()

        confirm_btn._cmd = _confirm
        choose_btn._cmd = _choose

    # ─────────────────────────────────────────────────────────────
    #  BROWSE
    # ─────────────────────────────────────────────────────────────
    def _show_browse(self):
        body, nav = self._build_shell("Student Portal – Browse")
        nav["Browse"]._col(nav["Browse"]._hbg)

        content = RF(body, r=12, bg=WH, bc=BORDER, bw=1.5)
        content.pack(side="left", fill="both", expand=True)

        # search bar
        top = tk.Frame(content.inner, bg=WH)
        top.pack(fill="x", padx=12, pady=(12,6))
        search_v = tk.StringVar()
        sch = RF(top, r=10, bg=WH, bc=BORDER, bw=1.5, height=36)
        sch.pack(fill="x")
        tk.Label(sch.inner, text="🔍", bg=WH, font=("Helvetica",13)).pack(side="left", padx=6)
        tk.Entry(sch.inner, textvariable=search_v, font=("Helvetica",11),
                 bg=WH, bd=0, highlightthickness=0, fg="#333").pack(
                 side="left", fill="both", expand=True, pady=4)

        # filter chips
        filt_frame = tk.Frame(content.inner, bg=WH)
        filt_frame.pack(fill="x", padx=12, pady=(0,6))
        active_filter = tk.StringVar(value="All")
        filter_opts = ["All","PDF","DOC","JPEG","PNG","CSV"]
        chip_btns = {}
        for opt in filter_opts:
            def _mkcmd(o=opt):
                def _f():
                    active_filter.set(o)
                    for k,b in chip_btns.items():
                        b._bg  = ACC if k==o else WH
                        b._hbg = "#3a6aaa" if k==o else "#e0e8f5"
                        b._fg  = WH if k==o else "#333"
                        b._bc  = "#3a6aaa" if k==o else BORDER
                        b._col(b._bg)
                    _refresh()
                return _f
            cb = RB(filt_frame, text=opt, r=8, width=58, height=26,
                    font=("Helvetica",9), cmd=_mkcmd(opt))
            cb.pack(side="left", padx=2)
            chip_btns[opt] = cb
        chip_btns["All"]._bg="#5588cc"; chip_btns["All"]._hbg="#3a6aaa"
        chip_btns["All"]._fg=WH; chip_btns["All"]._bc="#3a6aaa"
        chip_btns["All"]._col("#5588cc")

        # file list
        list_rf = RF(content.inner, r=10, bg="#fafafa", bc=BORDER, bw=1.5)
        list_rf.pack(fill="both", expand=True, padx=12, pady=(0,12))
        scroll_outer, scroll_inner = make_scrollable(list_rf.inner, bg="#fafafa")
        scroll_outer.pack(fill="both", expand=True)

        def _open_file(path):
            try:
                if sys.platform == "win32":   os.startfile(path)
                elif sys.platform == "darwin": subprocess.call(["open", path])
                else:                          subprocess.call(["xdg-open", path])
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        def _download(path, name):
            dest = filedialog.asksaveasfilename(
                initialfile=name,
                defaultextension=os.path.splitext(name)[1])
            if dest:
                shutil.copy2(path, dest)
                # Track download in database
                db.record_download(self.username, name)
                messagebox.showinfo("Downloaded", f"Saved to:\n{dest}")

        def _delete(name):
            if messagebox.askyesno("Delete", f"Delete '{name}'?"):
                try:
                    os.remove(os.path.join(UPLOADS_DIR, name))
                    db.delete_file_metadata(name)
                except Exception as ex:
                    messagebox.showerror("Error", str(ex))
                _refresh()

        def _refresh():
            for w in scroll_inner.winfo_children(): w.destroy()
            filt = active_filter.get()
            query = search_v.get().strip().lower()
            files = load_uploaded_files()
            shown = [f for f in files
                     if (filt=="All" or f["type"].upper()==filt.upper())
                     and (not query or query in f["name"].lower()
                          or query in f["course"].lower()
                          or query in f["topic"].lower())]
            if not shown:
                tk.Label(scroll_inner, text="No files found.",
                         bg="#fafafa", fg="#aaa",
                         font=("Helvetica",11)).pack(pady=40)
                return
            for f in shown:
                row = RF(scroll_inner, r=10, bg=WH, bc="#e0e0e0", bw=1, height=72)
                row.pack(fill="x", padx=8, pady=4)
                row.pack_propagate(False)

                color = TYPE_COLORS.get(f["type"], "#7f8c8d")
                ic = tk.Canvas(row.inner, width=44, height=44,
                               bg=WH, highlightthickness=0)
                ic.pack(side="left", padx=(10,8), pady=12)
                ic.create_oval(2,2,42,42, fill=color, outline="")
                ic.create_text(22,22, text=f["type"][:3], fill=WH,
                               font=("Helvetica",9,"bold"))

                info = tk.Frame(row.inner, bg=WH)
                info.pack(side="left", fill="both", expand=True, pady=8)
                tk.Label(info, text=f["name"], bg=WH, fg="#222",
                         font=("Helvetica",10,"bold"), anchor="w").pack(anchor="w")
                meta_txt = "  ".join(filter(None,[
                    f["course"] and f"📚 {f['course']}",
                    f["topic"]  and f"🏷 {f['topic']}",
                    f["uploader"] and f"👤 {f['uploader']}",
                    f["date"] and f"🗓 {f['date']}"
                ]))
                tk.Label(info, text=meta_txt or "No metadata", bg=WH,
                         fg="#888", font=("Helvetica",8), anchor="w").pack(anchor="w")

                acts = tk.Frame(row.inner, bg=WH)
                acts.pack(side="right", padx=8)
                RB(acts, text="View", r=7, width=54, height=26,
                   font=("Helvetica",9),
                   cmd=lambda fp=f["path"]: _open_file(fp)).pack(pady=(6,2))
                dl_row = tk.Frame(acts, bg=WH); dl_row.pack()
                RB(dl_row, text="⬇", r=7, width=30, height=24,
                   font=("Helvetica",10),
                   cmd=lambda fp=f["path"],fn=f["name"]: _download(fp,fn)).pack(side="left",padx=1)
                # Only admins can delete files
                if self.username == "admin":
                    RB(dl_row, text="🗑", r=7, width=30, height=24,
                       font=("Helvetica",10), bc="#ddaaaa", hbg="#fdecea",
                       cmd=lambda fn=f["name"]: _delete(fn)).pack(side="left",padx=1)

        search_v.trace_add("write", lambda *_: _refresh())
        _refresh()

    # ─────────────────────────────────────────────────────────────
    #  FORUMS
    # ─────────────────────────────────────────────────────────────
    def _show_forums(self):
        body, nav = self._build_shell("Student Portal – Forums")
        nav["Forums"]._col(nav["Forums"]._hbg)

        content = RF(body, r=12, bg=WH, bc=BORDER, bw=1.5)
        content.pack(side="left", fill="both", expand=True)

        # title row
        trow = tk.Frame(content.inner, bg=WH)
        trow.pack(fill="x", padx=16, pady=(14,6))
        tk.Label(trow, text="Discussion Forum", bg=WH, fg="#222",
                 font=("Helvetica",13,"bold")).pack(side="left")
        RB(trow, text="+ New Post", r=8, width=100, height=30,
           bg=ACC, hbg="#3a6aaa", fg=WH, bc="#3a6aaa",
           font=("Helvetica",9,"bold"),
           cmd=lambda: self._new_post_dialog(posts_inner, _refresh_posts)).pack(side="right")

        # post list
        pf = RF(content.inner, r=10, bg="#fafafa", bc=BORDER, bw=1.5)
        pf.pack(fill="both", expand=True, padx=16, pady=(0,14))
        scroll_outer, posts_inner = make_scrollable(pf.inner, bg="#fafafa")
        scroll_outer.pack(fill="both", expand=True)

        def _refresh_posts():
            for w in posts_inner.winfo_children(): w.destroy()
            posts = load_forum()
            if not posts:
                tk.Label(posts_inner, text="No posts yet. Be the first to post!",
                         bg="#fafafa", fg="#bbb",
                         font=("Helvetica",11)).pack(pady=40)
                return
            for post in reversed(posts):
                pcard = RF(posts_inner, r=10, bg=WH, bc="#e0e0e0", bw=1)
                pcard.pack(fill="x", padx=8, pady=5)
                ph = tk.Frame(pcard.inner, bg=WH)
                ph.pack(fill="x", padx=12, pady=(10,4))
                av_s = avatar_canvas(ph, size=32)
                av_s.pack(side="left")
                tk.Label(ph, text=post["author"], bg=WH, fg=ACC,
                         font=("Helvetica",10,"bold")).pack(side="left", padx=6)
                tk.Label(ph, text=post["date"], bg=WH, fg="#bbb",
                         font=("Helvetica",8)).pack(side="right")
                tk.Label(pcard.inner, text=post["title"], bg=WH, fg="#222",
                         font=("Helvetica",11,"bold"),
                         anchor="w").pack(anchor="w", padx=12)
                tk.Label(pcard.inner, text=post["body"], bg=WH, fg="#555",
                         font=("Helvetica",9), wraplength=580,
                         justify="left", anchor="w").pack(anchor="w", padx=12, pady=(2,10))

                # replies
                if post.get("replies"):
                    for rep in post["replies"]:
                        rep_f = tk.Frame(pcard.inner, bg="#f8f8f8",
                                         bd=0, relief="flat")
                        rep_f.pack(fill="x", padx=20, pady=(0,4))
                        tk.Label(rep_f, text=f"↳ {rep['author']}: {rep['body']}",
                                 bg="#f8f8f8", fg="#666",
                                 font=("Helvetica",9), anchor="w",
                                 wraplength=520).pack(anchor="w", padx=8, pady=2)

                # reply button
                rep_btn_frame = tk.Frame(pcard.inner, bg=WH)
                rep_btn_frame.pack(anchor="e", padx=12, pady=(0,8))
                RB(rep_btn_frame, text="Reply", r=6, width=62, height=24,
                   font=("Helvetica",8),
                   cmd=lambda p=post: self._reply_dialog(p, _refresh_posts)).pack()

        _refresh_posts()

    def _new_post_dialog(self, container, refresh_cb):
        dlg = tk.Toplevel(self.root)
        dlg.title("New Post"); dlg.geometry("480x340")
        dlg.configure(bg=BG); dlg.grab_set()

        RF_dlg = RF(dlg, r=16, bg=WH, bc=BORDER, bw=1.5)
        RF_dlg.place(relx=.5,rely=.5,anchor="center",width=440,height=310)
        i = RF_dlg.inner

        tk.Label(i, text="New Discussion Post", bg=WH, fg="#222",
                 font=("Helvetica",12,"bold")).pack(pady=(16,8))
        tk.Label(i, text="Title:", bg=WH, fg="#555",
                 font=("Helvetica",10), anchor="w").pack(anchor="w", padx=20)
        title_e = tk.Entry(i, font=("Helvetica",11), bg="#f9f9f9",
                           bd=1, relief="solid", highlightthickness=0)
        title_e.pack(fill="x", padx=20, ipady=4)
        tk.Label(i, text="Body:", bg=WH, fg="#555",
                 font=("Helvetica",10), anchor="w").pack(anchor="w", padx=20, pady=(8,0))
        body_t = tk.Text(i, font=("Helvetica",10), bg="#f9f9f9",
                         bd=1, relief="solid", height=5, wrap="word")
        body_t.pack(fill="x", padx=20)

        br = tk.Frame(i, bg=WH); br.pack(fill="x", padx=20, pady=10)

        def _submit():
            t = title_e.get().strip(); b = body_t.get("1.0","end").strip()
            if not t: messagebox.showwarning("Missing","Enter a title.",parent=dlg); return
            add_forum_post(self.username, t, b)
            messagebox.showinfo("Post Pending", 
                "Your post has been submitted!\nIt will be visible once approved by an admin.", parent=dlg)
            refresh_cb(); dlg.destroy()

        RB(br,"Cancel",r=8,width=100,height=32,cmd=dlg.destroy).pack(side="left",padx=(0,8))
        RB(br,"Post",r=8,width=100,height=32,bg=ACC,hbg="#3a6aaa",fg=WH,bc="#3a6aaa",
           cmd=_submit).pack(side="left")

    def _reply_dialog(self, post, refresh_cb):
        dlg = tk.Toplevel(self.root)
        dlg.title("Reply"); dlg.geometry("440x260")
        dlg.configure(bg=BG); dlg.grab_set()

        RF_dlg = RF(dlg, r=16, bg=WH, bc=BORDER, bw=1.5)
        RF_dlg.place(relx=.5,rely=.5,anchor="center",width=400,height=230)
        i = RF_dlg.inner
        tk.Label(i, text=f"Reply to: {post['title']}", bg=WH, fg="#222",
                 font=("Helvetica",11,"bold"), wraplength=340).pack(pady=(16,8), padx=16)
        body_t = tk.Text(i, font=("Helvetica",10), bg="#f9f9f9",
                         bd=1, relief="solid", height=4, wrap="word")
        body_t.pack(fill="x", padx=20)
        br = tk.Frame(i, bg=WH); br.pack(fill="x", padx=20, pady=10)

        def _submit():
            b = body_t.get("1.0","end").strip()
            if not b: return
            add_forum_reply(post["id"], self.username, b)
            messagebox.showinfo("Reply Pending", 
                "Your reply has been submitted!\nIt will be visible once approved by an admin.", parent=dlg)
            refresh_cb(); dlg.destroy()

        RB(br,"Cancel",r=8,width=100,height=32,cmd=dlg.destroy).pack(side="left",padx=(0,8))
        RB(br,"Reply",r=8,width=100,height=32,bg=ACC,hbg="#3a6aaa",fg=WH,bc="#3a6aaa",
           cmd=_submit).pack(side="left")

    # ─────────────────────────────────────────────────────────────
    #  DOWNLOADS
    # ─────────────────────────────────────────────────────────────
    def _show_downloads(self):
        body, nav = self._build_shell("Student Portal – Downloads")
        nav["Downloads"]._col(nav["Downloads"]._hbg)

        content = RF(body, r=12, bg=WH, bc=BORDER, bw=1.5)
        content.pack(side="left", fill="both", expand=True)

        tk.Label(content.inner, text="Your Downloads", bg=WH, fg="#222",
                 font=("Helvetica",13,"bold")).pack(anchor="w", padx=18, pady=(14,4))
        tk.Label(content.inner,
                 text="Files you have downloaded are listed here.",
                 bg=WH, fg="#888", font=("Helvetica",9)).pack(anchor="w", padx=18)

        list_rf = RF(content.inner, r=10, bg="#fafafa", bc=BORDER, bw=1.5)
        list_rf.pack(fill="both", expand=True, padx=18, pady=(10,14))
        scroll_outer, scroll_inner = make_scrollable(list_rf.inner, bg="#fafafa")
        scroll_outer.pack(fill="both", expand=True)

        # Get only files downloaded by this user
        downloaded_files = db.get_user_downloads(self.username)

        if not downloaded_files:
            tk.Label(scroll_inner, text="You haven't downloaded any files yet.\nBrowse files to download them.",
                     bg="#fafafa", fg="#bbb",
                     font=("Helvetica",11)).pack(pady=40)
            return

        all_files = load_uploaded_files()
        file_dict = {f["name"]: f for f in all_files}

        shown_any = False
        for filename in downloaded_files:
            if filename not in file_dict:
                continue  # ignore downloads where file is no longer available or not approved
            shown_any = True
            f = file_dict[filename]

            row = RF(scroll_inner, r=10, bg=WH, bc="#e0e0e0", bw=1, height=60)
            row.pack(fill="x", padx=8, pady=3)
            row.pack_propagate(False)
            color = TYPE_COLORS.get(f["type"],"#7f8c8d")
            ic = tk.Canvas(row.inner, width=36, height=36,
                           bg=WH, highlightthickness=0)
            ic.pack(side="left", padx=(10,8), pady=12)
            ic.create_oval(2,2,34,34, fill=color, outline="")
            ic.create_text(18,18, text=f["type"][:3], fill=WH,
                           font=("Helvetica",8,"bold"))
            info = tk.Frame(row.inner, bg=WH)
            info.pack(side="left", fill="both", expand=True)
            tk.Label(info, text=f["name"], bg=WH, fg="#222",
                     font=("Helvetica",10,"bold"), anchor="w").pack(anchor="w")
            try:
                sz = os.path.getsize(f["path"])
                s  = f"{sz/1024:.1f} KB" if sz<1048576 else f"{sz/1048576:.1f} MB"
            except Exception:
                s=""
            sub = " · ".join(filter(None,[s, f["course"], f["date"]]))
            tk.Label(info, text=sub, bg=WH, fg="#aaa",
                     font=("Helvetica",8)).pack(anchor="w")

            def _open_dl(fp=f["path"]):
                try:
                    if sys.platform == "win32":   os.startfile(fp)
                    elif sys.platform == "darwin": subprocess.call(["open", fp])
                    else:                          subprocess.call(["xdg-open", fp])
                except Exception as ex:
                    messagebox.showerror("Error", str(ex))

            RB(row.inner, text="📂 Open", r=7, width=106, height=28,
               font=("Helvetica",9), cmd=_open_dl).pack(side="right", padx=10)

        if not shown_any:
            tk.Label(scroll_inner, text="No downloaded files are available right now.\nTry downloading files from Browse.",
                     bg="#fafafa", fg="#bbb",
                     font=("Helvetica",11)).pack(pady=40)

    # ─────────────────────────────────────────────────────────────
    #  ADMIN PANEL
    # ─────────────────────────────────────────────────────────────
    def _show_admin_panel(self):
        body, nav = self._build_shell("Student Portal – Admin Panel")
        nav["Admin Panel"]._col(nav["Admin Panel"]._hbg)

        content = RF(body, r=12, bg=WH, bc=BORDER, bw=1.5)
        content.pack(side="left", fill="both", expand=True)

        # Tab selection
        tab_frame = tk.Frame(content.inner, bg=WH)
        tab_frame.pack(fill="x", padx=16, pady=(14,6))
        
        tk.Label(tab_frame, text="Admin Review", bg=WH, fg="#222",
                 font=("Helvetica",13,"bold")).pack(side="left")
        
        tab_btns = {}
        for tab_name in ["Files", "Posts", "Replies"]:
            b = RB(tab_frame, text=tab_name, r=8, width=80, height=28,
                   font=("Helvetica",9))
            b.pack(side="left", padx=4)
            tab_btns[tab_name] = b

        # Content area
        content_rf = RF(content.inner, r=10, bg="#fafafa", bc=BORDER, bw=1.5)
        content_rf.pack(fill="both", expand=True, padx=16, pady=(0,14))
        scroll_outer, scroll_inner = make_scrollable(content_rf.inner, bg="#fafafa")
        scroll_outer.pack(fill="both", expand=True)

        def _show_pending_files():
            for w in scroll_inner.winfo_children(): w.destroy()
            for tb in tab_btns.values(): tb._col(tb._bg)
            tab_btns["Files"]._bg = ACC
            tab_btns["Files"]._col(ACC)
            
            files = db.get_pending_files()
            if not files:
                tk.Label(scroll_inner, text="No pending files.",
                         bg="#fafafa", fg="#bbb",
                         font=("Helvetica",11)).pack(pady=40)
                return
            
            for f in files:
                row = RF(scroll_inner, r=10, bg=WH, bc="#e0e0e0", bw=1, height=100)
                row.pack(fill="x", padx=8, pady=4)
                row.pack_propagate(False)
                
                info_frame = tk.Frame(row.inner, bg=WH)
                info_frame.pack(fill="both", expand=True, padx=12, pady=8)
                tk.Label(info_frame, text=f"{f['filename']}", bg=WH, fg="#222",
                         font=("Helvetica",10,"bold"), anchor="w").pack(anchor="w")
                tk.Label(info_frame, text=f"📚 {f['course']} • 🏷 {f['topic']} • 👤 {f['uploader']} • 🗓 {f['upload_date']}", 
                         bg=WH, fg="#888", font=("Helvetica",8), anchor="w").pack(anchor="w")
                
                btn_frame = tk.Frame(row.inner, bg=WH)
                btn_frame.pack(anchor="e", padx=12, pady=(0,8))
                RB(btn_frame, text="👁 View", r=7, width=70, height=26,
                   font=("Helvetica",9), bg="#fff3cd", hbg="#ffeaa7",
                   cmd=lambda fn=f["filename"]: _view_file(fn)).pack(side="left", padx=2)
                RB(btn_frame, text="✅ Approve", r=7, width=90, height=26,
                   font=("Helvetica",9), bg="#d4edda", hbg="#c3e6cb",
                   cmd=lambda fn=f["filename"]: _approve_file(fn)).pack(side="left", padx=2)
                RB(btn_frame, text="❌ Reject", r=7, width=80, height=26,
                   font=("Helvetica",9), bg="#f8d7da", hbg="#f5c6cb",
                   cmd=lambda fn=f["filename"]: _reject_file(fn)).pack(side="left", padx=2)
                RB(btn_frame, text="🗑 Delete", r=7, width=80, height=26,
                   font=("Helvetica",9), bg="#f5c6cb", hbg="#f1ad96",
                   cmd=lambda fn=f["filename"]: _delete_file_admin(fn)).pack(side="left", padx=2)

        def _show_pending_posts():
            for w in scroll_inner.winfo_children(): w.destroy()
            for tb in tab_btns.values(): tb._col(tb._bg)
            tab_btns["Posts"]._bg = ACC
            tab_btns["Posts"]._col(ACC)
            
            pending = db.get_pending_forum_content()
            posts = pending["posts"]
            if not posts:
                tk.Label(scroll_inner, text="No pending posts.",
                         bg="#fafafa", fg="#bbb",
                         font=("Helvetica",11)).pack(pady=40)
                return
            
            for p in posts:
                row = RF(scroll_inner, r=10, bg=WH, bc="#e0e0e0", bw=1)
                row.pack(fill="x", padx=8, pady=4)
                row.pack_propagate(False)
                
                info_frame = tk.Frame(row.inner, bg=WH)
                info_frame.pack(fill="both", expand=True, padx=12, pady=8)
                tk.Label(info_frame, text=p['title'], bg=WH, fg="#222",
                         font=("Helvetica",10,"bold"), anchor="w").pack(anchor="w")
                tk.Label(info_frame, text=f"By {p['author']}", bg=WH, fg="#888",
                         font=("Helvetica",8), anchor="w").pack(anchor="w")
                tk.Label(info_frame, text=p['body'][:200], bg=WH, fg="#555",
                         font=("Helvetica",8), wraplength=500, anchor="w").pack(anchor="w")
                
                btn_frame = tk.Frame(row.inner, bg=WH)
                btn_frame.pack(anchor="e", padx=12, pady=(0,8))
                RB(btn_frame, text="✅ Approve", r=7, width=90, height=26,
                   font=("Helvetica",9), bg="#d4edda", hbg="#c3e6cb",
                   cmd=lambda pid=p["id"]: _approve_post(pid)).pack(side="left", padx=2)
                RB(btn_frame, text="❌ Reject", r=7, width=80, height=26,
                   font=("Helvetica",9), bg="#f8d7da", hbg="#f5c6cb",
                   cmd=lambda pid=p["id"]: _reject_post(pid)).pack(side="left", padx=2)

        def _show_pending_replies():
            for w in scroll_inner.winfo_children(): w.destroy()
            for tb in tab_btns.values(): tb._col(tb._bg)
            tab_btns["Replies"]._bg = ACC
            tab_btns["Replies"]._col(ACC)
            
            pending = db.get_pending_forum_content()
            replies = pending["replies"]
            if not replies:
                tk.Label(scroll_inner, text="No pending replies.",
                         bg="#fafafa", fg="#bbb",
                         font=("Helvetica",11)).pack(pady=40)
                return
            
            for r in replies:
                row = RF(scroll_inner, r=10, bg=WH, bc="#e0e0e0", bw=1)
                row.pack(fill="x", padx=8, pady=4)
                row.pack_propagate(False)
                
                info_frame = tk.Frame(row.inner, bg=WH)
                info_frame.pack(fill="both", expand=True, padx=12, pady=8)
                tk.Label(info_frame, text=f"Reply by {r['author']}", bg=WH, fg="#222",
                         font=("Helvetica",10,"bold"), anchor="w").pack(anchor="w")
                tk.Label(info_frame, text=r['body'][:200], bg=WH, fg="#555",
                         font=("Helvetica",8), wraplength=500, anchor="w").pack(anchor="w")
                
                btn_frame = tk.Frame(row.inner, bg=WH)
                btn_frame.pack(anchor="e", padx=12, pady=(0,8))
                RB(btn_frame, text="✅ Approve", r=7, width=90, height=26,
                   font=("Helvetica",9), bg="#d4edda", hbg="#c3e6cb",
                   cmd=lambda rid=r["id"]: _approve_reply(rid)).pack(side="left", padx=2)
                RB(btn_frame, text="❌ Reject", r=7, width=80, height=26,
                   font=("Helvetica",9), bg="#f8d7da", hbg="#f5c6cb",
                   cmd=lambda rid=r["id"]: _reject_reply(rid)).pack(side="left", padx=2)

        def _view_file(filename):
            filepath = os.path.join(UPLOADS_DIR, filename)
            if not os.path.exists(filepath):
                messagebox.showerror("Error", "File not found.")
                return
            
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                # Show image preview
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(filepath)
                    # Resize if too large
                    max_size = (800, 600)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Create preview window
                    preview = tk.Toplevel(self.root)
                    preview.title(f"Preview: {filename}")
                    preview.geometry("820x620")
                    preview.resizable(True, True)
                    
                    # Canvas for image
                    canvas = tk.Canvas(preview, bg="#333")
                    canvas.pack(fill="both", expand=True)
                    
                    photo = ImageTk.PhotoImage(img)
                    canvas.create_image(400, 300, image=photo, anchor="center")
                    
                    # Keep reference
                    canvas.image = photo
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Could not preview image: {str(e)}")
            else:
                # Open with default application
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(filepath)
                    else:
                        subprocess.run(['xdg-open', filepath])
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open file: {str(e)}")

        def _approve_file(filename):
            db.approve_file(filename, self.username)
            messagebox.showinfo("Approved", f"'{filename}' has been approved!")
            _show_pending_files()

        def _reject_file(filename):
            db.reject_file(filename, self.username, "Did not meet guidelines")
            messagebox.showinfo("Rejected", f"'{filename}' has been rejected!")
            _show_pending_files()

        def _delete_file_admin(filename):
            if messagebox.askyesno("Delete File", f"Permanently delete '{filename}'? This cannot be undone."):
                try:
                    filepath = os.path.join(UPLOADS_DIR, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    db.delete_file_metadata(filename)
                    messagebox.showinfo("Deleted", f"'{filename}' has been permanently deleted!")
                    _show_pending_files()
                except Exception as e:
                    messagebox.showerror("Error", f"Could not delete file: {str(e)}")

        def _approve_post(post_id):
            db.approve_forum_post(post_id, self.username)
            messagebox.showinfo("Approved", "Post has been approved!")
            _show_pending_posts()

        def _reject_post(post_id):
            db.reject_forum_post(post_id, self.username, "Violates community guidelines")
            messagebox.showinfo("Rejected", "Post has been rejected!")
            _show_pending_posts()

        def _approve_reply(reply_id):
            db.approve_forum_reply(reply_id, self.username)
            messagebox.showinfo("Approved", "Reply has been approved!")
            _show_pending_replies()

        def _reject_reply(reply_id):
            db.reject_forum_reply(reply_id, self.username, "Violates community guidelines")
            messagebox.showinfo("Rejected", "Reply has been rejected!")
            _show_pending_replies()

        # Set initial view
        for tb in tab_btns.values(): tb._cmd = None
        tab_btns["Files"]._cmd = _show_pending_files
        tab_btns["Posts"]._cmd = _show_pending_posts
        tab_btns["Replies"]._cmd = _show_pending_replies
        
        _show_pending_files()

# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    App()
