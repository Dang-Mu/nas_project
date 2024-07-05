import torch
import torch.nn as nn
import torch.nn.functional as F
import nni
from nni.nas.nn.pytorch import LayerChoice, ModelSpace, MutableDropout, MutableLinear

import nni.nas.strategy as strategy
from nni.nas.evaluator import FunctionalEvaluator
from nni.nas.experiment import NasExperiment


# 깊이별 분리 합성곱 계층
class DepthwiseSeparableConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.depthwise = nn.Conv2d(in_ch, in_ch, kernel_size=3, groups=in_ch)
        self.pointwise = nn.Conv2d(in_ch, out_ch, kernel_size=1)

    def forward(self, x):
        return self.pointwise(self.depthwise(x))

# 모델 스페이스
class MyModelSpace(ModelSpace):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        # LayerChoice is used to select a layer between Conv2d and DwConv.
        self.conv2 = LayerChoice([
            nn.Conv2d(32, 64, 3, 1),
            DepthwiseSeparableConv(32, 64)
        ], label='conv2')
        # nni.choice is used to select a dropout rate.
        # The result can be used as parameters of `MutableXXX`.
        self.dropout1 = MutableDropout(nni.choice('dropout', [0.25, 0.5, 0.75]))  # choose dropout rate from 0.25, 0.5 and 0.75
        self.dropout2 = nn.Dropout(0.5)
        feature = nni.choice('feature', [64, 128, 256])
        self.fc1 = MutableLinear(9216, feature)
        self.fc2 = MutableLinear(feature, 10)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(self.conv2(x), 2)
        x = torch.flatten(self.dropout1(x), 1)
        x = self.fc2(self.dropout2(F.relu(self.fc1(x))))
        output = F.log_softmax(x, dim=1)
        return output

# 모델 평가자
def evaluate_model(model):
    # By v3.0, the model will be instantiated by default.
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    transf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    train_loader = DataLoader(MNIST('data/mnist', download=True, transform=transf), batch_size=64, shuffle=True)
    test_loader = DataLoader(MNIST('data/mnist', download=True, train=False, transform=transf), batch_size=64)

    for epoch in range(3):
        # train the model for one epoch
        train_epoch(model, device, train_loader, optimizer, epoch)
        # test the model for one epoch
        accuracy = test_epoch(model, device, test_loader)
        # call report intermediate result. Result can be float or dict
        nni.report_intermediate_result(accuracy)

    # report final test result
    nni.report_final_result(accuracy)


def tutorial():
    model_space = MyModelSpace()
    search_strategy = strategy.GridSearch()  # dedup=False if deduplication is not wanted
    evaluator = FunctionalEvaluator(evaluate_model)
    exp = NasExperiment(model_space, evaluator, search_strategy)

    exp.config.max_trial_number = 4   # spawn 2 trials at most
    exp.config.trial_concurrency = 1  # will run 2 trial concurrently
    exp.config.trial_gpu_number = 0   # will not use GPU

    # exp.run(port=8081, wait_completion=False)

    # print(exp.strategy._status)

    # for model in exp.strategy.list_models():
    #     print(model)
    
    return exp