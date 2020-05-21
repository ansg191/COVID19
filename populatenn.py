import nnData as nn
from datetime import datetime
from glob import glob

nn_list = glob("assets/nn/*.csv")
start = max([int(x[19:-4]) for x in nn_list])

for i in range(start, (datetime.today() - datetime(2019, 12, 31)).days + 1):
    nn.pred_to_file2(i, extra_days=50, minimum=100)
