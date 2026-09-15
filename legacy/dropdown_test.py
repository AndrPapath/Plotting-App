# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

import tkinter as tk

root = tk.Tk()
options = ["Plain", "Parametric", "Histogram"]
var = tk.StringVar()
var.set(options[0])
om = tk.OptionMenu(root, var, *options)
om.pack()
root.mainloop()