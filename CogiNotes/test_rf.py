import tkinter as tk

# Test RF rendering
class RF(tk.Canvas):
    def __init__(self, parent, r=14, bg="white", **kw):
        super().__init__(parent, bg="gray", highlightthickness=0, **kw)
        self._r, self._bg = r, bg
        self.inner = tk.Frame(self, bg=bg)
        self._win = self.create_window(0, 0, window=self.inner, anchor="nw")
        self.bind("<Configure>", self._resize)
    
    def _resize(self, e):
        w, h = e.width, e.height
        w = max(3, w)
        h = max(3, h)
        self.delete("_bg")
        # Draw a simple rectangle
        self.create_rectangle(1, 1, w-1, h-1, fill=self._bg, outline="black", width=2)
        p = 5
        self.coords(self._win, p, p)
        self.itemconfig(self._win, width=max(1, w-p*2), height=max(1, h-p*2))

root = tk.Tk()
root.geometry("400x300")

outer = RF(root, bg="white")
outer.pack(fill="both", expand=True, padx=10, pady=10)

inner_frame = tk.Frame(outer.inner, bg="lightblue", height=50)
inner_frame.pack(fill="x")
inner_frame.pack_propagate(False)
tk.Label(inner_frame, text="Header", bg="lightblue").pack()

body_frame = tk.Frame(outer.inner, bg="lightyellow")
body_frame.pack(fill="both", expand=True)
tk.Label(body_frame, text="Body Content", bg="lightyellow").pack(expand=True)

root.mainloop()
