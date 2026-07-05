# TRAINING Garment model on the "ashraq/fashion-product-images-small" dataset

'''
new data: Each row has these fields, and the ones you care about are:
image — an actual image (varied sizes, ~53–60px per the metadata, color).
subCategory — broad bucket: Topwear, Bottomwear, etc.
articleType — the specific type: Shirts, Tshirts, Sweatshirts, Dresses, Jeans, Track Pants, etc.
    - label source
'''
from mlx import nn

from datasets import load_dataset
import numpy as np
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import numpy as np
from garment_model import GarmentNet 

# LOAD DATASETS!
ds = load_dataset("ashraq/fashion-product-images-small", split="train")

print(ds)                          # overall structure
print(ds[0].keys())                # what fields each row has
print(ds[0]["articleType"])        # the label field we'll use
print(ds[0]["subCategory"])
ds[0]["image"]                     # it's a PIL image object

# LABEL MAPPING
    # we decide what label in the data counts as what class for this model 
    # want only 4 classses
LABEL_MAP = {
    "Jeans": 0, "Track Pants": 0, "Trousers": 0, "Shorts": 0,   # → Pants (0)
    "Shirts": 3, "Tshirts": 3, "Sweatshirts": 3, # → Shirt (3)
    "Sweaters": 1, # → Sweater (1)
    "Dresses": 2, # → Dress (2)
}
class_names = ["Pants", "Sweater", "Dress", "Shirt"]   # index 0,1,2,3

# PREPROCESSING OF DATA
# resize images one 784 length row
# to 28x28, convert to grayscale, flatten to 784 pixels, and normalize to 0–1
def preprocess(dataset):
    images = []
    labels = []
    for row in dataset:
        article = row["articleType"]
        if article not in LABEL_MAP: # skip garments outside our 4 classes
            continue

        img = row["image"] # a PIL image, color, ~60px, varied size
        img = img.convert("L") # "L" = grayscale (1 channel instead of 3)
        img = img.resize((28, 28)) # force to fixed 28×28 so it's always 784 numbers

        arr = np.array(img, dtype=np.float32) # PIL image → numpy grid of 0–255
        arr = arr / 255.0  # normalize to 0–1
        arr = arr.flatten() # 28×28 grid → flat 784-length row

        images.append(arr)
        labels.append(LABEL_MAP[article])

    images = mx.array(np.stack(images))   # list of rows → one (N, 784) array
    labels = mx.array(labels)
    return images, labels

all_images, all_labels = preprocess(ds)
print("real garment train shape:", all_images.shape)   # (N, 784)
print("labels shape:", all_labels.shape)
print("number kept:", len(all_labels))

# CREATE TRAIN/TEST SPLIT
# hold data back so train on 80% of it and test on 20% of it that the model has never seen!
# shuffle data
np.random.seed(0) # reproducible shuffle
perm = np.random.permutation(len(all_labels)) # random order of all indices
all_images = all_images[mx.array(perm)] # apply shuffle to images
all_labels = all_labels[mx.array(perm)]   

split = int(0.8 * len(all_labels)) # 80% mark
train_images, train_labels = all_images[:split], all_labels[:split] # first 80%
test_images, test_labels  = all_images[split:], all_labels[split:] # last 20%
print("train:", train_images.shape, " test:", test_images.shape)

model = GarmentNet()

# LOSS FUNCTION
# so model(X) will give me 4 scores for each image in X
# this loss function will give: how wrong, as one number
def loss_fn(model, X, y):
    return mx.mean(nn.losses.cross_entropy(model(X), y))    
    # cross entropy returns loss for each image sperately so for a batch of 128 , it gives 128 loss values
    # need to collapse to one number so take mean

loss_and_grad = nn.value_and_grad(model, loss_fn)   # like mx.grad, but for a whole model
    #  computes gradients for ALL the model's weights at once and you dont have to unpack them manually
optimizer = optim.SGD(learning_rate=0.05) # does the "nudge weights" step for me, had to drop learning rate
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

# writes trained weights to a file
model.save_weights("garment_model.safetensors")

