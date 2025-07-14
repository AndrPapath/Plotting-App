import numpy as np
import matplotlib.pyplot as plt
import csv
from order_of_magnitude import order_of_magnitude
from pandas import *

# Plots data from the columns of the .csv file. Used for .csv files containing a parametric analysis.
# Each trace is labeled with the name and value of the parameter specified in its corresponding column's name
# The plot's legend is formatted properly and the parameter is displayed with its proper units and order of magnitude 

def my_sign(x):
    temp = (x > 0) - (x < 0)
    if temp >= 0:
        return ''
    else: 
        return '-'

def getLegend(str):
        temp= str[str.find('(')+1:str.find(')')]
        if temp[0] == 'I':
            unit = 'A'
        elif temp[0] == 'V':
            unit = 'V'
        else:
            unit = input("Parameter's units: ")
        number = float(temp[temp.find('=')+1:])
        number = my_sign(number) + order_of_magnitude.symbol(abs(number), scale=scale_)[2] + unit
        temp1 =  temp.replace(temp[temp.find('=')+1:], number)
        return '$' + temp1.replace(temp1[:temp1.find('=')], param_name) + '$'

path = input("CSV files path: ")
destpath = input("Destination path: ")

while(True):
    folderpath = input("File folder: ") 
    circuit = input("Circuit name: ")
    filename = input("File name: ")
    param_name = input("Parameter name (TeX format): ")
    scale_ = input("Parameter's scale: ")
    legend_loc = input("Legend Location: ")
    if legend_loc == '': legend_loc = 'best'
    #title = input("Plot title: ")
    title = ''
    x_label = input("Input name (TeX format): ")
    y_label = input("Output name (TeX format): ")
    x_norm = float(input("Normalize input: "))
    y_norm = float(input("Normalize output: "))
    names = np.array([])
    legend = np.array([])

    data = read_csv(path + folderpath + filename + '.csv')
    fig, ax = plt.subplots(figsize=(8, 6), layout='constrained')
    line = 2.4
    with open(path + folderpath  + filename + '.csv') as csv_file:
        csv_reader = list(csv.reader(csv_file, delimiter=','))
        name_index=0
        for name in csv_reader[0]:
            names = np.append(names, [name])
            if name_index == 0:
                x = data[names[0]].to_numpy()*x_norm
            #print(name)
            #print(name_index)
            if name_index != 0:
                #legend = np.append(legend, getLegend(name))
                #print()
                y = data[name].to_numpy()*y_norm
                ax.plot(x, y, label=getLegend(name), linewidth = line)
            name_index += 1

    font_size = 18
    
    
    ax.set_title(title)
    ax.grid(True)
    ax.legend(loc = legend_loc, fontsize=font_size-2)
    plt.xlabel(names[0])
    plt.ylabel('$' + y_label + '$', fontsize=font_size+4)
    plt.xlabel('$' + x_label + '$', fontsize=font_size+4)
    plt.xticks(fontsize=font_size)
    plt.yticks(fontsize=font_size)
    fig = plt.gcf()
    plt.show()
    in_save = ''
    while in_save != 'y' and in_save != 'n':
        in_save = input("Save to PDF? (y/n): ").lower()
    if in_save == 'y':
        fig.savefig(destpath + folderpath + circuit + '_' + filename + '.pdf')
        print("Saved in: " + destpath + folderpath + circuit + '_' + filename + '.pdf')
    in_cont = ''
    while in_cont != 'y' and in_cont != 'n':
        in_cont = input("Continue? (y/n): ").lower()
    if in_cont == 'y':
        continue
    elif in_cont == 'n':
        break