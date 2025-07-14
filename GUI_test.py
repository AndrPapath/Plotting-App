try:
    import csv
    from pandas import read_csv
    from tkinter import *
    from tkinter import filedialog as fd
    from tkinter.messagebox import showinfo
    import numpy as np
    import matplotlib
    from order_of_magnitude import order_of_magnitude
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
except ModuleNotFoundError as e:
        print('The necessary Python packages are not installed.\n' + str(e))

def my_sign(x):
    temp = (x > 0) - (x < 0)
    if temp >= 0:
        return ''
    else: 
        return '-'

def plot_refresh(dummy=''):
     axs.grid(grid.get())
     axs.set_title(titleEntry.get(), fontsize=fontEntry.get())
     axs.set_xlabel(xaxisEntry.get(), fontsize=fontEntry.get())
     axs.set_ylabel(yaxisEntry.get(), fontsize=fontEntry.get())
     axs.tick_params(axis='x', labelsize=fontEntry.get())
     axs.tick_params(axis='y', labelsize=fontEntry.get())
     plot_legend()
     canvas.draw()
     
def plot_clear():
     axs.clear()
     remove_legend()
     canvas.draw()

def remove_legend():
     fig.legends = []
     lgnd = axs.get_legend()
     if lgnd != None:
        lgnd.remove()

def plot_legend():
     font = legendFontEntry.get()
     loc_ = loc.get()
     if v.get() > 0:
          cols=1
     else:
          cols=len(axs.lines)
     remove_legend()
     if plotLegend.get():
          if loc_[0] != 'o':
               axs.legend(loc=loc_, ncols=cols, fontsize=float(font)*0.8)
          else:
            fig.legend(loc=loc_, ncols=cols, fontsize=float(font)*0.8)

def panel_refresh(option):
     for List in plainItems, paramItems, histItems:
        for item in List:
          item.grid_remove()
     if option == "Parametric":
          for item in paramItems:
               item.grid()
     elif option == "Plain":
          for item in plainItems:
               item.grid()
     elif option == "Histogram":
          for item in histItems:
               item.grid()
     else: 
          for item in plainItems:
               item.grid()

def plot_draw():
     if plotMode.get() == "Parametric":
         oldlist = list(traces.keys())
         newlist = ['x_data']
         for name in oldlist[1:]:
             newlist.append(getLegend(name))
         temp = dict(zip(newlist, list(traces.values())))
         traces_param.clear()
         traces_param.update(temp)
         traces_ = traces_param
     else:
         traces_ = traces
     scale_x = int(float(xscaleEntry.get()))
     scale_y = int(float(yscaleEntry.get()))

     for (label, trace) in traces_.items():
        if label == 'x_data':
          x_data = traces_[label]
        else:
          axs.plot(x_data*scale_x, trace*scale_y, label=label)
     plot_refresh()
     #canvas.draw()

def getLegend(title):
        param_name = paramNameEntry.get().split("'")
        unit = unitEntry.get().split(',')
        scale_=scaleEntry.get().split(',')
        out = []
        names = []
        if param_name == '':
          return "MISSING LABEL NAME"
        temp= title[title.find('(')+1:title.find(')')] # Get the part of the title inside the parentheses, usually the parameter values
        param_list = temp.split("'")
        for str_ in param_list:
            name = str_[0:str_.find('=')]
            if not (name in names):
                names.append(name)
        if paramNameEntry.get() == '':
            paramNameEntry.delete(0,END)
            paramNameEntry.insert(0,', '.join(names))
        param_name = paramNameEntry.get().split(", ")
        if len(scale_) < len(param_list):
            for i in range(len(param_list)-len(scale_)):
                scale_.append(None)
        if len(unit) < len(param_list):
            for i in range(len(param_list)-len(unit)):
                unit.append('')
        for i in range(len(param_list)):
          str_=param_list[i]
          number = float(str_[str_.find('=')+1:]) # Grab the parameter's value
          number = my_sign(number) + order_of_magnitude.symbol(abs(number), scale=scale_[i])[2] + unit[i] # Rewrite number on the specified order of magnitude with its units
          temp1 =  str_.replace(str_[str_.find('=')+1:], number) # Replace the original number in the label
          out.append(temp1.replace(temp1[:temp1.find('=')], param_name[i]))
        return '$' + ', '.join(out) + '$'

def get_data(filename):
     data = read_csv(filename)
     name_index=0
     with open(filename) as csv_file:
        csv_reader = list(csv.reader(csv_file, delimiter=','))
        for name in csv_reader[0]:
            if name_index == 0:
                traces.update({'x_data': data[name].to_numpy()})
            else:
                y = data[name].to_numpy()
                traces.update({name: y})
            name_index += 1
     return name_index

def select_file():
    filetypes = (
        ('Comma-separated values', '*.csv'),
        ('All files', '*.*')
    )

    filename = fd.askopenfilename(
        title='Open a file',
        initialdir='/',
        filetypes=filetypes)

    get_data(filename)
    paramNameEntry.delete(0,END)
    unitEntry.delete(0,END)
    scaleEntry.delete(0,END)
    
    showinfo(
        title='Selected File',
        message=filename
    )

root = Tk() 
root.title('CSV Plotting Tool')

minGraph_y=300
minGraph_x=300
minPanel_x = 100
root.rowconfigure(1, weight=1, minsize=minGraph_y)
root.columnconfigure(0, weight=1, minsize=minGraph_x)
root.columnconfigure(1, minsize=minPanel_x)
#root.resizable(False, False)
root.minsize(minGraph_x+minPanel_x+10, minGraph_y+50)

options = [
     "Plain",
     "Parametric",
     "Histogram"
]

legendLoc = [
    'best',
    'upper left',
    'upper center',
    'upper right',
    'lower left',
    'lower center',
    'lower right',
    'outside upper left',
    'outside upper center',
    'outside upper right',
    'outside lower left',
    'outside lower center',
    'outside lower right',
    'outside left upper',
    'outside left center',
    'outside left lower',
    'outside right upper',
    'outside right center',
    'outside right lower',
]

legendRadioValues = {"Horizontal" : -1,
          "Vertical" : 1,
}

fontVar = IntVar()
fontVar.set(14)
legendFontVar = IntVar()
legendFontVar.set(10)
v = IntVar()
v.set(1)
plotMode = StringVar() 
plotMode.set(options[0])
loc = StringVar() 
loc.set(legendLoc[0]) 
grid = BooleanVar() 
grid.set(True) 

global fig, axs, traces

traces = {}
traces_param = {}

fig = Figure(figsize = (5, 4), dpi = 100, layout='constrained') 
# adding the subplot 
axs = fig.add_subplot()
# plotting the graph 
axs.plot() 

# Canvas 
canvas = FigureCanvasTkAgg(fig, master=root) 
canvas.draw() 
# creating the Matplotlib toolbar 
toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False,)
toolbar.update() 

# Panels
sidePanel = Frame(master=root, relief='sunken', borderwidth=5)
sidePanelLabel_plain = Label(master=sidePanel, text='Plain')
sidePanelLabel_param = Label(master=sidePanel, text='Parametric Set')
sidePanelLabel_hist = Label(master=sidePanel, text='Histogram')
topPanel = Frame(master=root, relief='raised', borderwidth=5)

# Buttons
loadButton = Button(root, text='Load', width=25, command=select_file)
plotButton = Button(topPanel, text='Plot', width=5, command=lambda: plot_draw())
replaceButton = Button(topPanel, text='Replace', width=5, command=lambda: [plot_clear(), plot_draw()])
clearButton = Button(topPanel, text='Clear', width=5, command=plot_clear)

# Side panel Content
# Common
titleEntryLabel = Label(master=sidePanel, text="Plot title:")
titleEntry = Entry(master=sidePanel)
xaxisEntryLabel = Label(master=sidePanel, text="x axis label:")
xaxisEntry = Entry(master=sidePanel)
yaxisEntryLabel = Label(master=sidePanel, text="y axis label:")
yaxisEntry = Entry(master=sidePanel)
plotLegend= BooleanVar()
legendCheck = Checkbutton(master=sidePanel, text="Show legend:", variable=plotLegend, 
                          onvalue=True, offvalue=False, command=plot_refresh)
gridCheck = Checkbutton(master=sidePanel, text="Grid", variable=grid, 
                          onvalue=True, offvalue=False, command=plot_refresh)
xscaleEntryLabel = Label(master=sidePanel, text="Scale x axis:")
xscaleEntry = Entry(master=sidePanel)
xscaleEntry.insert(0, 1)
yscaleEntryLabel = Label(master=sidePanel, text="Scale y axis:")
yscaleEntry = Entry(master=sidePanel)
yscaleEntry.insert(0, 1)
legendLocDrop = OptionMenu(sidePanel , loc , *legendLoc, command=plot_refresh)
fontEntryLabel = Label(sidePanel, text="Font size:")
fontEntry = Spinbox(sidePanel, from_=0, to=100, command=plot_refresh, textvariable=fontVar)
legendFontEntryLabel = Label(sidePanel, text="Legend font size:")
legendFontEntry = Spinbox(sidePanel, from_=0, to=100, command=plot_refresh, textvariable=legendFontVar)

commonItems = [
     titleEntryLabel, titleEntry, 
     xaxisEntryLabel, xaxisEntry, 
     yaxisEntryLabel, yaxisEntry, 
     fontEntryLabel, fontEntry, 
     legendFontEntryLabel, legendFontEntry,
     legendCheck, legendLocDrop, 
     None, None, 
     gridCheck, None, 
     xscaleEntryLabel, xscaleEntry, 
     yscaleEntryLabel, yscaleEntry
]

i=0
row = commonItems.index(legendLocDrop)//2+1
for (text, value) in legendRadioValues.items(): 
    Radiobutton(sidePanel, text = text, variable = v, 
        value = value, command=plot_refresh).grid(row=row, column=i, sticky='nsew')
    i+=1

# Parametric
paramNameEntryLabel = Label(master=sidePanel, text="Parameter's name:")
paramNameEntry = Entry(master=sidePanel)
unitEntryLabel = Label(master=sidePanel, text="Parameter's units:")
unitEntry = Entry(master=sidePanel)
scaleEntryLabel = Label(master=sidePanel, text="Parameter's scale (mili, micro etc.):")
scaleEntry = Entry(master=sidePanel)

# Menus
plotTypeDrop = OptionMenu(root , plotMode , *options, command=panel_refresh)





# Panels, Canvas
sidePanel.grid(row=1, column=1, sticky='nsew')

sidePanelLabel_plain.grid(row=0, column=0, sticky='nsw')
sidePanelLabel_param.grid(row=0, column=0, sticky='nsw')
sidePanelLabel_hist.grid(row=0, column=0, sticky='nsw')

canvas.get_tk_widget().grid(row=1, column=0, sticky='nsew')
topPanel.grid(row=0, column=0, sticky='nswe')
toolbar.grid(row=2, column=0, sticky='nsew')

# Side Panel Content
# Common
# titleEntryLabel.grid(row=1, column=0, sticky='nsew')
# titleEntry.grid(row=1, column=1, sticky='nsew')
# xaxisEntryLabel.grid(row=2, column=0, sticky='nsew')
# xaxisEntry.grid(row=2, column=1, sticky='nsew')
# yaxisEntryLabel.grid(row=3, column=0, sticky='nsew')
# yaxisEntry.grid(row=3, column=1, sticky='nsew')
# legendCheck.grid(row=4, column=0, sticky='nsew')
# legendLocDrop.grid(row=4, column=1, sticky='nsew')
# gridCheck.grid(row=6, column=0, sticky='nsew')
# xscaleEntryLabel.grid(row=7, column=0, sticky='nsew')
# xscaleEntry.grid(row=7, column=1, sticky='nsew')
# yscaleEntryLabel.grid(row=8, column=0, sticky='nsew')
# yscaleEntry.grid(row=8, column=1, sticky='nsew')

for i in range(len(commonItems)):
     if commonItems[i] != None:
          row=i//2
          commonItems[i].grid(row=row, column=i%2, sticky='nsew')

# Parametric
paramNameEntryLabel.grid(row=row+1, column=0, sticky='nsew')
paramNameEntry.grid(row=row+1, column=1, sticky='nsew')
unitEntryLabel.grid(row=row+2, column=0, sticky='nsew')
unitEntry.grid(row=row+2, column=1, sticky='nsew')
scaleEntryLabel.grid(row=row+3, column=0, sticky='nsew')
scaleEntry.grid(row=row+3, column=1, sticky='nsew')

# Buttons
loadButton.grid(row=2, column=1, sticky='nsew')
plotButton.grid(row=0, column=0, sticky='nw')
replaceButton.grid(row=0, column=1, sticky='nw')
clearButton.grid(row=0, column=2, sticky='nw')


plainItems = [sidePanelLabel_plain]
paramItems = [sidePanelLabel_param, paramNameEntryLabel, paramNameEntry, 
              unitEntryLabel, unitEntry, scaleEntryLabel, scaleEntry]
histItems = [sidePanelLabel_hist]

for List in paramItems, histItems:
     for item in List:
          item.grid_remove()

# Menus
plotTypeDrop.grid(row=0, column=1, sticky='nsew')

root.mainloop() 
