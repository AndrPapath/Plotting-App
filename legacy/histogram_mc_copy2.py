# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import matplotlib.pyplot as plt
from pandas import read_excel

font = 14
while True:
    filename = input("File name: ")
    N_of_intervals = int(input("No. of intervals: "))
    data = read_excel(filename, usecols="A:C")
    

    data_ = [data.to_numpy()*100]
    print(data)
    names = []
    for column in data:
        print(column)
        total_min = round(float(min(data[column]))*100,2)
        total_max = round(float(max(data[column]))*100,2)

        range_ = total_max-total_min
        interval = round(range_/N_of_intervals,2)
        class_centers = []
        class_labels = []
        N_of_class = []
        lowers = []
        uppers = []
        lower = total_min
        for i in range(N_of_intervals):
            if i<N_of_intervals-1:
                upper = lower + interval - 0.01
            else: upper = lower + interval
            lowers.append(round(lower, 2))
            uppers.append(round(upper, 2))
            mid = round(lower + interval/2,2)
            class_centers.append(mid)
            class_labels.append(str(round(lower, 2)) + "-\n" + str(round(upper, 2)))
            lower = upper + 0.01

        N_of_class = {column: np.zeros(N_of_intervals)}


        for element in data[column]:
            element = round(element,2)
            for i in range(len(lowers)):
                if element >= lowers[i] and element <= uppers[i]:
                    N_of_class[column][i] += 1

    x = np.arange(N_of_intervals)
    width = 0.45 # the width of the bars
    multiplier = 0


    fig, ax = plt.subplots(figsize=(5, 4), layout='constrained')
    for attribute, measurement in N_of_class.items():
        offset = width * multiplier
        rects = ax.bar(x + offset, measurement, width, color='olivedrab')
        #ax.bar_label(rects, padding=3)
        multiplier += 1

    # Add some text for labels, title and custom x-axis tick labels, etc.
    plt.xlabel('Classification Accuracy (%)', fontsize=font)
    plt.ylabel('No of iterations', fontsize=font)
    plt.yticks(fontsize=font)
    ax.set_xticks(x, class_labels, rotation=45, fontsize=font)
    plt.grid(axis='y')
    #ax.legend()

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