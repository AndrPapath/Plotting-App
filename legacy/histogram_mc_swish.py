# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import matplotlib.pyplot as plt
from pandas import read_excel
from matplotlib.ticker import EngFormatter, PercentFormatter, AutoMinorLocator

font = 14
while True:
    #filename = "C:/Users/andrp/OneDrive/Έγγραφα/IC/Projects/OJCAS_ISCAS Invited/ojcasinvitedpaper20iterandmc/dataset_1_mc_OJCAS_Invited_ANN_clf.xlsx"
    #filename2 = "C:/Users/andrp/OneDrive/Έγγραφα/IC/Projects/ICM 2025/Swish/swish_mc_0_2.xlsx"
    filename = input("File name: ")
    N_of_intervals = int(input("No. of bins: "))
    data = read_excel(filename, usecols="A")#:C")
    #scatter = read_excel(filename2)
    color = 'xkcd:orangered'
    style1 = {'facecolor': color, 'alpha': 0.6}
    style2 = {'facecolor': 'none', 'edgecolor': color, 'linewidth': 2}

    data_ = [data.to_numpy()]
    #print(data)
    fig, ax = plt.subplots(figsize=(5, 4), layout='constrained')
    ax.grid(True)
    plt.hist(data*100, bins=N_of_intervals, **style1)
    plt.hist(data*100, bins=N_of_intervals, **style2)
    #plt.scatter(scatter["X"]*1e9, scatter["Y"], alpha=0.7, facecolor='firebrick')

    #plt.title("$I_{in}=0nA$", fontsize=font)
    plt.xticks(fontsize=font)
    plt.yticks(fontsize=font)
    plt.xlabel('Classification Accuracy', fontsize=font)
    plt.ylabel('Number of iterations', fontsize=font)


    #ax.xaxis.set_major_formatter(EngFormatter(unit='%'))
    ax.xaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.xaxis.set_minor_locator(AutoMinorLocator())

    plt.show()
    if input("Save to PDF? (y/n): ") == 'y':
        fig.savefig(filename.replace('xlsx', 'pdf'))
    in_cont = ''
    while in_cont != 'y' and in_cont != 'n':
        in_cont = input("Continue? (y/n): ")
    if in_cont == 'y':
        continue
    elif in_cont == 'n':
        break
    # names = []
    # for header in data:
    #     #print(column)
    #     total_min = float(min(data[header]))
    #     total_max = float(max(data[header]))
    #     print(f"total min: {total_min}, total max: {total_max}")

    #     range_ = total_max-total_min
    #     print(f"range: {range}")
    #     interval = range_/N_of_intervals
    #     print(f"interval: {interval}")
    #     class_centers = []
    #     class_labels = []
    #     N_of_class = []
    #     lowers = []
    #     uppers = []
    #     lower = total_min
    #     for i in range(N_of_intervals):
    #         if i<N_of_intervals-1:
    #             upper = lower + 0.99*interval
    #         else: upper = lower + interval
    #         lowers.append(lower)
    #         uppers.append(upper)
    #         mid = lower + interval/2
    #         class_centers.append(mid)
    #         class_labels.append(str(round(lower*1e9,2)) + " $-$ " + str(round(upper*1e9,2)))
    #         lower = upper + 0.01*interval

    #     N_of_class = {header: np.zeros(N_of_intervals)}

    #     print(uppers)
    #     print(lowers)

    #     for element in data[header]:
    #         for i in range(len(lowers)):
    #             if element >= lowers[i] and element <= uppers[i]:
    #                 N_of_class[header][i] += 1

    # x = np.arange(N_of_intervals)
    # width = 0.45 # the width of the bars
    # multiplier = 0


    # fig, ax = plt.subplots(figsize=(5, 4), layout='constrained')
    # for attribute, measurement in N_of_class.items():
    #     offset = width * multiplier
    #     rects = ax.bar(x + offset, measurement, width, color='orangered')
    #     #ax.bar_label(rects, padding=3)
    #     multiplier += 1

    # # Add some text for labels, title and custom x-axis tick labels, etc.
    # plt.xlabel('Error (nA)', fontsize=font)
    # plt.ylabel('No of iterations', fontsize=font)
    # plt.yticks(fontsize=font)
    # ax.set_xticks(x, class_labels, rotation=60, fontsize=font)
    # #labels= ['Software', 'Proposed']
    # plt.grid(axis='y')
    # #ax.legend()

    # fig = plt.gcf()
    # print(f"{N_of_class} -> sum={np.sum(N_of_class["mc_0"])}")
    # plt.show()
    # if input("Save to PDF? (y/n): ") == 'y':
    #     fig.savefig(filename.replace('xlsx', 'pdf'))
    # in_cont = ''
    # while in_cont != 'y' and in_cont != 'n':
    #     in_cont = input("Continue? (y/n): ")
    # if in_cont == 'y':
    #     continue
    # elif in_cont == 'n':
    #     break