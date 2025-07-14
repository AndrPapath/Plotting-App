import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcol
from pandas import read_excel

font=14
while True:
    filename = input("File name: ")
    N_of_bins = int(input("No. of bins: "))
    data = read_excel(filename, usecols="A:B")

    software = data["Software"].to_numpy()*100
    hardware = data["Hardware"].to_numpy()*100
    print(software)

    total_min = round(min(np.min(software), np.min(hardware)),2)
    total_max = round(max(np.max(software), np.max(hardware)),2)
    print(f"Total min: {total_min}")
    print(f"Total max: {total_max}")


    range_ = total_max-total_min
    interval = range_/N_of_bins

    class_centers = []
    class_labels = []
    N_of_class = []
    lowers = []
    uppers = []
    lower = total_min
    for i in range(N_of_bins):
        if i<N_of_bins-1:
            upper = lower + interval - 0.01
        else: 
            upper = lower + interval
        lowers.append(round(lower, 2))
        uppers.append(round(upper, 2))
        mid = round(lower + interval/2,2)
        class_centers.append(mid)
        class_labels.append(str(round(lower, 2)) + "-\n" + str(round(upper, 2)))
        lower = upper + 0.01
    print(f"Interval: {interval}")
    print(f"lower limits: {lowers}")
    print(f"upper limits: {uppers}")

    N_of_class = {
        'SW' : np.zeros(N_of_bins),
        'HW' : np.zeros(N_of_bins)
    }

    for element in hardware:
        element = round(element,2)
        for i in range(len(lowers)):
            if element >= lowers[i] and element <= uppers[i]:
                N_of_class['HW'][i] += 1
                
    for element in software:
        element = round(element,2)
        for i in range(len(lowers)):
            if element >= lowers[i] and element <= uppers[i]:
                N_of_class['SW'][i] += 1

    x = np.arange(N_of_bins)
    width = 0.4 # the width of the bars
    multiplier = 0


    fig, ax = plt.subplots(figsize=(5, 4), layout='constrained')
    for attribute, measurement in N_of_class.items():
        offset = width * multiplier
        if attribute=='HW':
            col='indianred'
        else:
            col='sandybrown'
        rects = ax.bar(x + offset, measurement, width, label=attribute, color=col)
        multiplier += 1

    # Add some text for labels, title and custom x-axis tick labels, etc.
    plt.xlabel('Classification Accuracy (%)', fontsize=font)
    plt.ylabel('Number of iterations', fontsize=font)
    plt.yticks(fontsize=font)
    ax.set_xticks(x + width/2, class_labels, rotation=45, fontsize=font)
    labels= ['Software', 'Proposed']
    plt.grid(axis='y')
    ax.legend(labels, loc='best', ncols=1, fontsize=font-2)
    #fig.legend(labels, loc='outside upper center', ncols=2, fontsize=font-2)

    fig = plt.gcf()
    print(f"SW: {N_of_class['SW']} -> sum={np.sum(N_of_class['SW'])}")
    print(f"HW: {N_of_class['HW']} -> sum={np.sum(N_of_class['HW'])}")
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