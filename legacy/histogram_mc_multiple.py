# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import matplotlib.pyplot as plt
from pandas import read_excel

font = 14
while True:
    filename = input("File name: ")
    bins = int(input("No. of bins: "))
    data = read_excel(filename, usecols='A:C')
    data_ = [data.to_numpy()*100]
    #print(data)
    
    names = []
    total_max = 0
    total_min= 100
    for column in data_:
        #print(column)
        total_min = min(round(np.min(column),2), total_min)
        total_max = max(round(np.max(column),2), total_max)

    range_ = total_max-total_min
    interval = round(range_/bins,2)
    
    N_of_class = {}
    
    class_centers = []
    class_labels = []
    lowers = []
    uppers = []
    lower = total_min
    for i in range(bins):
        if i<bins-1:
            upper = lower + interval - 0.01
        else: upper = lower + interval
        lowers.append(round(lower, 2))
        uppers.append(round(upper, 2))
        mid = round(lower + interval/2,2)
        class_centers.append(mid)
        class_labels.append(str(round(lower, 2)) + "-\n" + str(round(upper, 2)))
        lower = upper + 0.01
    fig, ax = plt.subplots(figsize=(5, 4), layout='constrained')
    for count, head in enumerate(data):
        column = data[head]
        print(column)
        N_of_class[head] = np.zeros(bins)

        for element in column:
            element = round(100*float(element),2)
            for i in range(len(lowers)):
                if element >= lowers[i] and element <= uppers[i]:
                    N_of_class[head][i] += 1

        x = np.arange(bins)
        print(x)
        width = 0.3 # the width of the bars, changed from 0.3 to 0.6 xx
        multiplier = -1

        colors = ['peru', 'olivedrab', 'steelblue', 'purple', 'crimson', 'darkslategray', 'coral']
    #print(N_of_class.items())
    for attribute, measurement in N_of_class.items():
        multiplier += 1
        offset = width * multiplier
        rects = ax.bar(x + offset, measurement, width, color=colors[multiplier+1], label = attribute)

    # Add some text for labels, title and custom x-axis tick labels, etc.
    
    plt.xlabel('Classification Accuracy (%)', fontsize=font)
    plt.ylabel('No of iterations', fontsize=font)
    plt.yticks(fontsize=font)
    print(len(N_of_class))
    ax.set_xticks(x+(len(N_of_class)-1)*width/2, class_labels, rotation=45, fontsize=font) # x+... subject to change! xx
    #ax.set_ylim([0, 13])
    plt.grid(axis='y')
    ax.legend(loc='upper left')

    fig = plt.gcf()
    print(N_of_class)
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