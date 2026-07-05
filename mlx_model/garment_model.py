import mlx.nn as nn

# DEFINE THE MODEL (which hear is a neural network blueprint)
# nn.Module is the base class for all neural network blueprints
    # nn.Module tracks all the weights for me! (where in line fit we tracked m and b manually)
class GarmentNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Linear(784, 64) # 784 inputs → 64 
        self.layer2 = nn.Linear(64, 4)  # 64 → 4 outputs (one per class)

    def __call__(self, x):
        x = self.layer1(x) # first linear transform
        x = nn.relu(x) # the activation — bend it so it can learn twisty relationships
            # this just makes input that are negative → 0, positive → unchanged.
        x = self.layer2(x) # final transform → 4 scores
        return x