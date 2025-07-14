import csv
from matplotlib.backend_bases import FigureCanvasBase
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
import matplotlib
from order_of_magnitude import order_of_magnitude
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

class ScrollableFrame(Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas = Canvas(self)
        self.scrollbar = Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<MouseWheel>", self.OnMouseWheel)
    
    def OnMouseWheel(self,event):
        self.scrollbar.yview("scroll",event.delta,"units")
        return "break" 

class Window(Toplevel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        #self.minsize(width=500, height=500)
        self.title('Traces')
        self.row_counter = 0
        self.trace_counter = 0
        self.bg = ScrollableFrame(self)
        self.bg.grid(row=0, column=0, sticky=NSEW)
        fr = []

        for index, trace in enumerate(data):
            fr.append(LabelFrame(self.bg.scrollable_frame, text=f"Trace {self.trace_counter}"))
            fr[index].grid(row=self.row_counter, column=0, sticky='nsew', pady=5, padx=5)
            Label(fr[index], text="Name: ").grid(row=self.row_counter, column=0, sticky=W, pady=5)
            Entry(fr[index], textvariable=trace.name).grid(row=self.row_counter, column=1, pady=5)
            Label(fr[index], text="Visible: ").grid(row=self.row_counter, column=2, sticky=W, pady=5)
            Checkbutton(fr[index], variable=trace.visible, onvalue=True, offvalue=False).grid(row=self.row_counter, column=3, sticky=W, pady=5)
            Label(fr[index], text="Plot on twin Y axis").grid(row=self.row_counter+1, column=2, sticky=W, pady=5)
            Checkbutton(fr[index], variable=trace.twinx, onvalue=True, offvalue=False).grid(row=self.row_counter+1, column=3, sticky=W, pady=5)
            Radiobutton(fr[index], text="Set as X axis", variable=parent.x_axis, value=self.trace_counter).grid(row=self.row_counter, column=6, sticky=W, pady=5)
            Label(fr[index], text="Scale Trace: ").grid(row=self.row_counter+1, column=0, sticky=W, pady=5)
            Entry(fr[index], textvariable=trace.scale).grid(row=self.row_counter+1, column=1, pady=5)
            Button(fr[index], text="Delete", command=fr[trace.index].destroy).grid(row=self.row_counter+1, column=4, pady=5)

            self.trace_counter += 1
            self.row_counter += 2
        
        #Button(self, text='Close', command=self.destroy).grid(row=self.row_counter, column=0, pady=5, sticky=SEW)

class Trace:
    def __init__(self, label, data, index):
        self.data = data
        self.index = index
        self.name = StringVar(value=label)
        self.visible = BooleanVar(value=True)
        self.color = None
        self.scale = StringVar(value="1")
        self.twinx = BooleanVar(value=False)
    
    def set_visible(self, val):
        self.visible.set(val)

    def is_visible(self):
        return self.visible.get()
    
    def set_name(self, label):
        self.name.set(label)

    def get_name(self):
        return self.name.get()
    
    def get_scale(self):
        try:
            return float(self.scale.get())
        except Exception as e:
            print(f"Trace scale error: {e}")
            return 1
    
    def set_scale(self, val):
        self.scale.set(val)

    def on_twin_x(self):
        return self.twinx.get()

class PlottingApp(Tk):
    # def __init__(self, root):
    #     self.root = root
    #     self.root
    def __init__(self):
        super().__init__()
        
        self.title('CSV Plotting Tool')
        minGraph_y=300
        minGraph_x=300
        minPanel_x = 100
        self.rowconfigure(1, weight=1, minsize=minGraph_y)
        self.columnconfigure(0, weight=1, minsize=minGraph_x)
        self.columnconfigure(1, minsize=minPanel_x)
        #root.resizable(False, False)
        self.minsize(minGraph_x+minPanel_x+10, minGraph_y+50)

        self.filename = ''
        self.options = [
            "Plain",
            "Parametric",
            "Histogram"
        ]

        self.legendLoc = [
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

        self.legendRadioValues = {"Horizontal" : -1,
                "Vertical" : 1,
        }

        self.x_axis = IntVar(value=0)
        self.row_counter=0
        self.grid = BooleanVar() 
        self.grid.set(True)
        self.plot_title_var = StringVar()
        self.x_axis_label_var = StringVar()
        self.y_axis_label_var = StringVar()
        self.twin_x_axis_label_var = StringVar()
        self.font_var = IntVar(value=14)
        self.width_var = IntVar(value=1)
        self.legend_font_var = IntVar(value=10)
        self.grid_var = BooleanVar(value=True)
        self.logy_var = BooleanVar(value=False)
        self.logx_var = BooleanVar(value=False)
        self.color_y_axes = BooleanVar(value=False)
        self.default_colors_var = BooleanVar(value=True)
        self.plot_legend_var = BooleanVar(value=False)
        self.legend_location_var = StringVar(value=self.legendLoc[0]) 
        self.legend_orientation_var = IntVar(value=1)
        self.x_scale_entry_var = StringVar(value=1)
        self.y_scale_entry_var = StringVar(value=1)
        self.x_ticks_entry_var = StringVar(value=0)
        self.xmin = StringVar(value=0)
        self.xmax = StringVar(value=0)
        self.param_name_var = StringVar()
        self.unit_var = StringVar()
        self.param_scale_var = StringVar()

        self.common_items_config = {
            "Plot Title": {"var": self.plot_title_var, "widget": Entry},
            "X Axis Label": {"var": self.x_axis_label_var, "widget": Entry},
            "Y Axis Label": {"var": self.y_axis_label_var, "widget": Entry},
            "Secondary Y Axis Label": {"var": self.twin_x_axis_label_var, "widget": Entry},
            "Font Size": {"var": self.font_var, "widget": Spinbox, "options": {"from_": 1, "to": 24}},
            "Legend Font Size": {"var": self.legend_font_var, "widget": Spinbox, "options": {"from_": 1, "to": 24}},
            "Grid": {"var": self.grid_var, "widget": Checkbutton, 
                     "options": {"onvalue": True, "offvalue": False}
                     },
            "Legend": {"var": self.plot_legend_var, "widget": Checkbutton},
            "Legend Location": {"var": self.legend_location_var, 
                                "options": {"value": self.legendLoc[0]}, 
                                "values": self.legendLoc,
                                "widget": OptionMenu},
            "Horizontal": {"var": self.legend_orientation_var, "widget": Radiobutton, "options": {"value": -1, }},
            "Vertical": {"var": self.legend_orientation_var, "widget": Radiobutton, 
                                "options": {"value": 1}},
            "Axes have Trace Color": {"var": self.color_y_axes, "widget": Checkbutton, 
                     "options": {"onvalue": True, "offvalue": False}
                     },
            "Default Trace Colors": {"var": self.default_colors_var, "widget": Checkbutton, 
                     "options": {"onvalue": True, "offvalue": False}
                     },
            "Scale X Axis": {"var": self.x_scale_entry_var, "widget": Entry},
            "Scale Y Axis": {"var": self.y_scale_entry_var, "widget": Entry},
            "Log Y Axis": {"var": self.logy_var, "widget": Checkbutton, 
                     "options": {"onvalue": True, "offvalue": False}
                     },
            "Log X Axis": {"var": self.logx_var, "widget": Checkbutton, 
                     "options": {"onvalue": True, "offvalue": False}
                     },
            "X tick interval": {"var": self.x_ticks_entry_var, "widget": Entry},
            "Min X": {"var": self.xmin, "widget": Entry},
            "Max X": {"var": self.xmax, "widget": Entry},
            "Line Width": {"var": self.width_var, "widget": Spinbox, "options": {"from_": 1, "to": 24}},
        }

        self.parametric_items_config = {
            "Parameter's Name": {"var": self.param_name_var, "widget": Entry},
            "Units": {"var": self.unit_var, "widget": Entry},
            "Parameter's Scale (mili, micro etc.)": {"var": self.param_scale_var, "widget": Entry},
        }

        self.histogram_items_config = {}

        self.side_panel = ScrollableFrame(self, relief='sunken', borderwidth=5)
        self.side_panel.grid(row=1, column=1, sticky='nsew')

        self.panel_plain = Frame(master=self.side_panel.scrollable_frame)
        self.panel_parametric = Frame(master=self.side_panel.scrollable_frame)
        self.panel_histogram = Frame(master=self.side_panel.scrollable_frame)

        self.current_panel = None  # To keep track of the currently displayed panel

        self.fig = Figure(figsize=(5, 4), dpi=100, layout='constrained')
        self.axs = self.fig.add_subplot()
        self.twin_x_axs = self.axs.twinx()
        self.color1 = 'red'
        self.color2 = 'red'
        self.line1 = None
        self.line2 = None

        self.create_canvas()

        self.traces = []
        self.traces_param = []

        self.plot_mode = StringVar() 
        self.plot_mode.set(self.options[0])
        self.plotTypeDrop = OptionMenu(self , self.plot_mode , *self.options, command=self.switch_panel)
        self.plotTypeDrop.grid(row=0, column=1, sticky='nsew')

        self.create_gui()

    def open_trace_window(self, traces):
        window = Window(self, traces)
        #window.grab_set()

    def create_canvas(self):
        #self.canvas_frame = Frame(master=self.root)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        #self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        self.toolbar.update()
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky='nsew')
        self.toolbar.grid(row=2, column=0, sticky='nsew')

    def create_gui(self):
        # ... your existing GUI creation code ...

        self.create_side_panel()
        self.create_top_panel()

    def create_side_panel(self):
        self.create_common_items(self.panel_plain)
        self.create_parametric_items(self.panel_parametric)
        self.create_histogram_items(self.panel_histogram)

        self.switch_panel("Plain")  # Display the default panel

    def create_top_panel(self):
        # ... your existing code for creating the top panel ...
        topPanel = Frame(master=self, relief='raised', borderwidth=5)

        # Buttons
        loadButton = Button(self, text='Load', width=25, command=self.select_file)
        plotButton = Button(topPanel, text='Plot', width=5, command=lambda: self.plot_draw())
        replaceButton = Button(topPanel, text='Replace', width=5, command=lambda: [self.plot_clear(), self.plot_draw()])
        clearButton = Button(topPanel, text='Clear', width=5, command=self.plot_clear)

        loadButton.grid(row=2, column=1, sticky='nsew')
        plotButton.grid(row=0, column=0, sticky='nw')
        replaceButton.grid(row=0, column=1, sticky='nw')
        clearButton.grid(row=0, column=2, sticky='nw')
        topPanel.grid(row=0, column=0, sticky='nswe')
        return
    
    def create_common_items(self, panel):
        self.row_counter = 0
        self.create_items(panel, self.common_items_config)
        # Create a button (customize as needed)
        Button(panel, text="Refresh", command=self.plot_refresh).grid(row=self.row_counter, column=0, columnspan=2, pady=5)

    def create_parametric_items(self, panel):
        self.row_counter = 0
        self.create_items(panel, self.common_items_config)
        self.create_items(panel, self.parametric_items_config)
        # Create a button (customize as needed)
        Button(panel, text="Refresh", command=self.plot_refresh).grid(row=self.row_counter, column=0, columnspan=2, pady=5)

    def create_histogram_items(self, panel):
        self.row_counter = 0
        self.create_items(panel, self.common_items_config)
        self.create_items(panel, self.histogram_items_config)
        # Create a button (customize as needed)
        Button(panel, text="Refresh", command=self.plot_refresh).grid(row=self.row_counter, column=0, columnspan=2, pady=5)
        
    def create_items(self, panel, items):
        for label, config in items.items():
            Label(panel, text=label).grid(row=self.row_counter, column=0, sticky=W, pady=5)

            widget_type = config["widget"]
            options = config.get("options", {})  # Additional options for the widget
            if widget_type == Entry or widget_type==Spinbox:
                    varname = "textvariable"
            else: varname = "variable"
            if widget_type != Entry:
                options["command"] = self.plot_refresh
            options[varname] = config["var"]
            if widget_type == OptionMenu:
                widget = OptionMenu(panel, options["variable"], *config.get("values"))
                widget.grid(row=self.row_counter, column=1, pady=5)
            else:
                widget = widget_type(panel, **options)
                widget.grid(row=self.row_counter, column=1, pady=5)

            self.row_counter += 1

    def switch_panel(self, panel_type):
        # Hide the current panel if it exists
        if self.current_panel is not None:
            self.current_panel.grid_remove()

        # Show the selected panel
        if panel_type == "Plain":
            self.panel_plain.grid()
            self.current_panel = self.panel_plain
        elif panel_type == "Parametric":
            self.panel_parametric.grid()
            self.current_panel = self.panel_parametric
        elif panel_type == "Histogram":
            self.panel_histogram.grid()
            self.current_panel = self.panel_histogram

    # ... your other methods ...
    def my_sign(self, x):
        temp = (x > 0) - (x < 0)
        if temp >= 0:
            return ''
        else: 
            return '-'
        
    def get_color_from_cycle(self, index):
        # Get the default color cycle
        default_color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
        
        # Ensure that the index is within bounds
        if 0 <= index < len(default_color_cycle):
            # Return the i-th color from the cycle
            return default_color_cycle[index]
        else:
            # Handle the case where the index is out of bounds
            return 'black'


    def plot_refresh(self):
        self.update_plot_properties()
        self.plot_legend()
        self.canvas.draw()

    def update_plot_properties(self):
        # Change the default filename for saving
        self.fig.canvas.get_default_filename = lambda: self.filename
        matplotlib.rcParams['savefig.format'] = 'pdf'

        if self.color_y_axes.get() == True:
            if self.line1 != None:
                self.color1 = self.line1.get_color()
            if self.line2 != None:
                self.color2 = self.line2.get_color()
        else: 
            self.color1 = 'black'
            self.color2 = 'black'
        self.axs.grid(self.grid_var.get())
        self.axs.set_title(self.plot_title_var.get(), fontsize=self.font_var.get())
        self.axs.set_xlabel(self.x_axis_label_var.get(), fontsize=self.font_var.get())
        self.axs.set_ylabel(self.y_axis_label_var.get(), fontsize=self.font_var.get(), color = self.color1)
        self.twin_x_axs.set_ylabel(self.twin_x_axis_label_var.get(), fontsize=self.font_var.get(), color = self.color2)
        self.twin_x_axs.yaxis.set_label_position("right")
        if self.logy_var.get():
            self.axs.set_yscale('log')
        else:
            self.axs.set_yscale('linear')
        if self.logx_var.get():
            self.axs.set_xscale('log')
        else:
            self.axs.set_xscale('linear')
        self.axs.tick_params(axis='x', labelsize=self.font_var.get())
        self.axs.tick_params(axis='y', labelsize=self.font_var.get(), color = self.color1, labelcolor = self.color1)
        self.twin_x_axs.tick_params(axis='y', labelsize=self.font_var.get(), color = self.color2, labelcolor = self.color2)
        #self.axs.set_yticks(np.linspace(self.axs.get_ybound()[0], self.axs.get_ybound()[1], 5))
        self.twin_x_axs.set_yticks(np.linspace(self.twin_x_axs.get_ybound()[0], self.twin_x_axs.get_ybound()[1], 5))
        # 
        #     if self.color1 != None:
        #         self.axs.tick_params(axis='y', color=self.color1.get_color())
        #     if self.color2 != None:
        #         self.twin_x_axs.tick_params(axis='y', color=self.color2.get_color())
     
    def plot_clear(self):
        self.twin_x_axs.clear()
        self.axs.clear()
        self.remove_legend()
        self.canvas.draw()

    def remove_legend(self):
        self.fig.legends = []
        lgnd = self.axs.get_legend()
        if lgnd is not None:
            lgnd.remove()

    def plot_legend(self):
        font = self.legend_font_var.get()
        loc_ = self.legend_location_var.get()
        cols = 1 if self.legend_orientation_var.get() > 0 else len(self.axs.lines)

        self.remove_legend()

        if self.plot_legend_var.get():
            if loc_[0] != 'o':
                self.axs.legend(loc=loc_, ncols=cols, fontsize=float(font) * 0.8)
            else:
                self.fig.legend(loc=loc_, ncols=cols, fontsize=float(font) * 0.8)

    def panel_refresh(self, option):
        for lst in [self.plain_items, self.param_items, self.hist_items]:
            for item in lst:
                item.grid_remove()
        if option == "Parametric":
            for item in self.param_items:
                item.grid()
        elif option == "Plain":
            for item in self.plain_items:
                item.grid()
        elif option == "Histogram":
            for item in self.hist_items:
                item.grid()
        else:
            for item in self.plain_items:
                item.grid()

    def plot_draw(self):
        try:
            self.color1 = 'red'
            self.color2 = 'red'
            self.twin_x_axs.set_axis_off()
        except Exception as e:
            print("No twin axis found")
        mode = self.plot_mode.get()
        if mode == "Parametric":
            for trace in self.traces:
                trace.set_name(self.get_Legend(trace.get_name()))
        scale_x = float(self.x_scale_entry_var.get())
        scale_y = float(self.y_scale_entry_var.get())

        x_data_trace = self.traces[self.x_axis.get()]
        x_data = x_data_trace.data
        for indx, trace in enumerate(self.traces):
            if trace.is_visible() == True:
                if trace.on_twin_x() == True:
                    self.twin_x_axs.set_axis_on()
                    self.color2 = self.get_color_from_cycle(indx-1)
                    self.line2, = self.twin_x_axs.plot(x_data*scale_x, trace.data*scale_y*trace.get_scale(), 
                                                       label=trace.get_name(), color = self.color2, 
                                                       linewidth = self.width_var.get())
                else:
                    if self.default_colors_var.get():
                        self.color1 = None
                    else:
                        self.color1 = self.get_color_from_cycle(indx-1)
                    self.line1, = self.axs.plot(x_data*scale_x, trace.data*scale_y*trace.get_scale(), 
                                                label=trace.get_name(), color = self.color1,
                                                linewidth = self.width_var.get())
                xmin = float(self.xmin.get())
                xmax = float(self.xmax.get())
                if float(self.x_ticks_entry_var.get()) > 0:
                    self.axs.xaxis.set_ticks(np.arange(xmin, xmax, step=float(self.x_ticks_entry_var.get())))
        self.plot_refresh()

        #canvas.draw()

    def get_Legend(self, title):
            param_name = self.param_name_var.get().split("'")
            unit = self.unit_var.get().split(',')
            scale_= self.param_scale_var.get().split(',')
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
            if self.param_name_var.get() == '':
                self.param_name_var.set("")
                self.param_name_var.set(', '.join(names))
            param_name = self.param_name_var.get().split(", ")
            if len(scale_) < len(param_list):
                for i in range(len(param_list)-len(scale_)):
                    scale_.append(None)
            if len(unit) < len(param_list):
                for i in range(len(param_list)-len(unit)):
                    unit.append('')
            for i in range(len(param_list)):
                str_=param_list[i]
            number = float(str_[str_.find('=')+1:]) # Grab the parameter's value
            number = self.my_sign(number) + order_of_magnitude.symbol(abs(number), scale=scale_[i])[2] + unit[i] # Rewrite number on the specified order of magnitude with its units
            temp1 =  str_.replace(str_[str_.find('=')+1:], number) # Replace the original number in the label
            out.append(temp1.replace(temp1[:temp1.find('=')], param_name[i]))
            return '$' + ', '.join(out) + '$'
    
    def get_data(self, filename):
        try:
            data = pd.read_csv(filename)
            name_index=0
            with open(filename) as csv_file:
                csv_reader = list(csv.reader(csv_file, delimiter=','))
                for index, name in enumerate(csv_reader[0]):
                    # if name_index == 0:
                    #     self.traces.update({'x_data': data[name].to_numpy()})
                    # else:
                    y = data[name].to_numpy()
                    #self.traces.update({name: y})
                    self.traces.append(Trace(name, y, index))
                    name_index += 1
            return
        except UnicodeDecodeError:
            data =pd.read_excel(filename)
            name_index=0
            for index, name in enumerate(data.columns.ravel()):
                # if name_index == 0:
                #     self.traces.update({'x_data': data[name].to_numpy()})
                #     print(data[name].to_numpy())
                # else:
                y = data[name].to_numpy()
                #self.traces.update({name: y})
                self.traces.append(Trace(name, y, index))
                name_index += 1
            return
        except Exception as e:
            print(f"An Error occurred: {e}")
            

    FILE_TYPES = [('Comma-separated values', '*.csv'), ("Excel files", ".xlsx .xls"), ('All files', '*.*')]
    def select_file(self):
        try:
            filetypes=self.FILE_TYPES
            self.filename = fd.askopenfilename(
                title='Open a file',
                initialdir='/',
                filetypes=filetypes)
            
            backup = self.traces
            self.traces  = []
            self.get_data(self.filename)
            self.param_name_var.set("")
            self.unit_var.set("")
            self.param_scale_var.set("")
            self.color1='black'
            self.color2='black'
            # showinfo(
            #     title='Selected File',
            #     message=filename
            # )
        except Exception as e:
            print(f"An error occurred: {e}")
            self.traces = backup #Restore traces in case of error loading the file
            # Handle the error gracefully, e.g., show a message box to the user
        finally:
            backup.clear()
            self.open_trace_window(self.traces)

if __name__ == "__main__":
    #root = Tk()
    app = PlottingApp()
    app.mainloop()