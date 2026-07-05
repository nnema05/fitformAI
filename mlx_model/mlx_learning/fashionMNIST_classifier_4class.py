# STEP 1: use fashion MNIST dataset
# FASHION MNIST is a dataset of 70,000 tiny grayscale images of clothing items (0 through 9), each 28×28 pixels
# every image has a label telling you which clothing item it is!
# goal: Each image is a 28×28 grid of numbers, where each number is a pixel's brightness (0 = black, 255 = white).
# feed in those 784 numbers (28×28 = 784), and have the network output "this is a 7."

'''
Fashion-MNIST has 10 classes with these indices:
0 T-shirt/top   1 Trouser   2 Pullover   3 Dress   4 Coat
5 Sandal        6 Sneaker   7 Shirt      8 Bag     9 Ankle boot
For FitForm's four (shirt/dress/sweater/pants), the natural matches are:

Pullover (2) ≈ sweater
Dress (3) ≈ dress
Trouser (1) ≈ pants
Shirt (7) ≈ shirt
'''

'''
784 pixels
   ↓  layer1 (Linear 784→64): combine pixels into 64 summary numbers
   ↓  ReLU activation: bend, so this isn't just a straight-line layers stacked and flattening into each other
        allows for findging complicated, twisty input to answer relationships
64 summaries
   ↓  layer2 (Linear 64→10): turn summaries into 10 digit-scores
10 scores → "it's a 7"
'''

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import numpy as np
import mlx_model.mlx_learning.mnist as mnist # Apple's official loader file
    # downloads data, reshapes to (N, 784)
    # It normalizes pixels to 0–1 (divides by 255)

# REDUCE TO ACTUAL LABLE WE WANT
LABEL_MAP = {1: 0, 2: 1, 3: 2, 7: 3}  # Trouser, Pullover, Dress, Shirt
# class_names = ["T-shirt/top","Trouser","Pullover","Dress","Coat", "Sandal","Shirt","Sneaker","Bag","Ankle boot"]
class_names = ["Pants", "Sweater", "Dress", "Shirt"]   # new 0,1,2,3 in order
def filter_and_relabel(images, labels):
    keep = []                                  # which rows to keep
    new_labels = []                            # their remapped labels
    labels_list = labels.tolist()              # to plain Python for easy checking
    for i, old in enumerate(labels_list):
        if old in LABEL_MAP:                   # is this one of our 4 classes?
            keep.append(i)
            new_labels.append(LABEL_MAP[old])  # remap 1→0, 2→1, 3→2, 7→3
    keep = mx.array(keep)
    return images[keep], mx.array(new_labels)  # filtered images + clean labels

# loaders public function returns 4 tensors diretcly  
# Returns four numpy arrays; wrap them as MLX arrays.
train_images, train_labels, test_images, test_labels = map(mx.array, mnist.fashion_mnist())
train_images, train_labels = filter_and_relabel(train_images, train_labels)
test_images, test_labels = filter_and_relabel(test_images, test_labels)

print("filtered train images shape:", train_images.shape)   # (60000, 784)
    # 60000 images, each flattened to 784 pixels
print("filtered labels shape:", train_labels.shape)   # (60000,)

# DEFINE THE MODEL (which hear is a neural network blueprint)
# nn.Module is the base class for all neural network blueprints
    # nn.Module tracks all the weights for me! (where in line fit we tracked m and b manually)
class MNISTNet(nn.Module):
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

model = MNISTNet()

# LOSS FUNCTION
# so model(X) will give me 4 scores for each image in X
# this loss function will give: how wrong, as one number
def loss_fn(model, X, y):
    return mx.mean(nn.losses.cross_entropy(model(X), y))    
    # cross entropy returns loss for each image sperately so for a batch of 128 , it gives 128 loss values
    # need to collapse to one number so take mean

loss_and_grad = nn.value_and_grad(model, loss_fn)   # like mx.grad, but for a whole model
    #  computes gradients for ALL the model's weights at once and you dont have to unpack them manually
optimizer = optim.SGD(learning_rate=0.1)            # does the "nudge weights" step for me
    # optim.SGD performs weight = weight - lr*grad for every weight automatically
    # SGD = "stochastic gradient descent,

# TRAINING LOOP
# first we will batch
    # so a small chunk of images processed together instead of 60,000 at once which is more faster and helps leanring 
def batches(images, labels, batch_size=128): 
    # added randomly shuffles the order of images every epoch.
        # Shuffling matters because if the model always sees images in the same order and same batches, it can learn quirks of that ordering instead of the digits themselves
        # forces it to learn actual patterns
    perm = mx.array(np.random.permutation(len(images)))
    for i in range(0, len(images), batch_size):
        X = mx.array(images[perm[i:i+batch_size]])
        y = mx.array(labels[perm[i:i+batch_size]])
        yield X, y

# epoch = one pass through the entire dataset, we have to do many epochs to learn
for epoch in range(10):                     # originally 5, changed to 10 to get closer to accuracy of .97
    for X, y in batches(train_images, train_labels):
        loss, grads = loss_and_grad(model, X, y) # forward + gradient
        optimizer.update(model, grads) # step: nudge weights downhill
        mx.eval(model.parameters(), optimizer.state) # force computation (bc mlx has lazy eval!)

    predictions = mx.argmax(model(test_images), axis=1) # pick highest-scoring digit
    accuracy = mx.mean(predictions == test_labels) # compare against the labels we have
    print(f"epoch {epoch}: test accuracy {accuracy.item():.3f}")

# this is similar has line fit!
# forward -> loss -> grad -> step but manua nugding goes to optimzier and we have a lot more weights here!
# accuracy = .965!

# PEEK AT A FEW PREDICTIONS 
predictions = mx.argmax(model(test_images), axis=1)  # model's guess for every test image

for i in range(10): # look at the first 10 test images
    guess = class_names[predictions[i].item()]  # what the model predicted
    truth = class_names[test_labels[i].item()]  # the real label
    mark = "✓" if guess == truth else "✗"       # correct or not
    print(f"{mark}  predicted: {guess:12s}  actual: {truth}")
