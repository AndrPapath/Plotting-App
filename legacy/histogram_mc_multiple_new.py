# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import matplotlib.pyplot as plt
from pandas import read_excel

font = 14
while True:
    filename = input("File name: ")
    bins = 0#int(input("No. of bins: "))
    data = read_excel(filename)#, usecols='A')
    data_ = [data.to_numpy()*100]
    print(data)
    
    # names = []
    # total_max = 0
    # total_min= 100
    # for column in data_:
    #     #print(column)
    #     total_min = min(round(np.min(column),2), total_min)
    #     total_max = max(round(np.max(column),2), total_max)

    # range_ = total_max-total_min
    # interval = round(range_/bins,2)
    
    # N_of_class = [np.zeros(bins)]
    
    # class_centers = []
    # class_labels = []
    # lowers = []
    # uppers = []
    # lower = total_min
    # for i in range(bins):
    #     if i<bins-1:
    #         upper = lower + interval - 0.01
    #     else: upper = lower + interval
    #     lowers.append(round(lower, 2))
    #     uppers.append(round(upper, 2))
    #     mid = round(lower + interval/2,2)
    #     class_centers.append(mid)
    #     class_labels.append(str(round(lower, 2)) + "-\n" + str(round(upper, 2)))
    #     lower = upper + 0.01
    fig, ax = plt.subplots(figsize=(5, 4), layout='constrained')
    # class_names=[]
    # for count, head in enumerate(data):
    # #     column = data[head]
    # #     print(column)
    # #     N_of_class[count] = np.zeros(bins)
    #     class_names.append(head)

    # #     for element in column:
    # #         element = round(100*float(element),2)
    # #         for i in range(len(lowers)):
    # #             if element >= lowers[i] and element <= uppers[i]:
    # #                 N_of_class[count][i] += 1

    # total_min /= 100
    # total_max /= 100
    # x = np.arange(start=total_min, stop=total_max, step= (total_max-total_min)/bins)
    #     print(x)
    #     width = 0.3 # the width of the bars, changed from 0.3 to 0.6 xx
    #     multiplier = -1

    colors = ['peru', 'olivedrab', 'steelblue', 'purple', 'crimson', 'darkslategray']
    #print(N_of_class.items())
    # for attribute, measurement in N_of_class.items():
    #     multiplier += 1
    #     offset = width * multiplier
        #rects = ax.bar(x + offset, measurement, width, color=colors[multiplier+1], label = attribute)
        #ax.bar_label(rects, padding=3)

    # Add some text for labels, title and custom x-axis tick labels, etc.
    
    plt.xlabel('$I_{out}/I_{in}$', fontsize=font)
    plt.ylabel('No of iterations', fontsize=font)
    plt.yticks(fontsize=font)
    colors_with_alpha = list(zip(colors, [0.3 for color in colors]))

    for ind, column in enumerate(data):
        style = {'facecolor': colors_with_alpha[ind], 'edgecolor': colors[ind], 'linewidth': 3}
        ax.hist(data[column], histtype='barstacked', **style, label=column)
    #ax.set_xticks(x+0.013, class_labels, rotation=45, fontsize=font) # x+... subject to change! xx
    #ax.set_xticks(fontsize=font)
    plt.grid(axis='y')
    fig.legend(loc='outside upper center', ncols=2)

    fig = plt.gcf()
    #print(N_of_class)
    plt.show()
    if input("Save to PDF? (y/n): ") == 'y':
        fig.savefig(filename + '.pdf')
    in_cont = ''
    while in_cont != 'y' and in_cont != 'n':
        in_cont = input("Continue? (y/n): ")
    if in_cont == 'y':
        continue
    elif in_cont == 'n':
        break