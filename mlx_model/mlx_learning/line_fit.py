# Fit a line to points with gradient descent 
''' Goal: we have some dots that roughly follow a line
A line is is y = m*x + b, we are going to pretend we dont know m and b and start with bad gueses
# let the gradeint descent algo dsicover them by going downhill 
'''

import mlx.core as mx

# DATA POINTS FOR LINE
# The "true" line we're pretending not to know: y = 2x + 1
# (slope 2, intercept 1)
x = mx.array([0.0, 1.0, 2.0, 3.0, 4.0])
y = mx.array([1.0, 3.0, 5.0, 7.0, 9.0])   # each is 2*x + 1

# INITIAL GUESS
# our initial guesses for slope and intercept wrong 
    # In MLX, a single number wrapped into an array framework is officially classified as a 0-dimension (0D) array or a scalar array
m = mx.array(0.0)
b = mx.array(0.0)

# MODEL AND LOSS FUNCTION
# guess --> measure wrongness loop!
    # m*x + b is the model, it predicts a y for every x
    # errors is exactly how wrong each prediction is to the actual y we know
    # we square the errors (so negative errors don't cancel out positive ones) and average them to get one number that tells us how wrong we are overall. This is called the loss function.
def loss_fn(m, b):
    predictions = m * x + b  # the model's guess for every x
    errors = predictions - y # how far off each guess is
    return mx.mean(errors ** 2)  # average squared error → one number

# print("starting loss:", loss_fn(m, b)) # large number, height on the hill we are stanidng
    # remember hill is: horizontal axis = the value of that weight
    # vertical axis = the loss (how wrong the model is)
    # you want the value of the weight that gives you the lowest loss, the bottom of the hill. You are going to take steps downhill to get there!
    # starting loss: array(33, dtype=float32)

# GRADIENT (MLX magic! )
# mx.grad turns a function into a NEW function that returns gradients.
    # basically it doesnt compute a number it hands you back a function 
    # you call function with the current m and b and it tells you the slope of loss with respect to each!
        # to reduce loss, nudge m this way and b that way
# argnums=(0, 1) means "give me the slope with respect to BOTH m and b."
grad_fn = mx.grad(loss_fn, argnums=(0, 1))
# grads = grad_fn(m, b)
# print("gradients:", grads)
    # gradients: (array(-28, dtype=float32), array(-10, dtype=float32))

# GRADIENT DESCENT LOOP
# we are going to take steps downhill to reduce loss
    # loop finds answer by seeing slope and stepping downhill a hundred times!
    # entire:  guess → loss → gradient → step → repeat cycle!
learning_rate = 0.05      # the step size
    # if learning rate is too big it will overshoot (.5), loss will bounce around and explode
    # if learning rate is too small (.001), convergence will be very slow 
for step in range(100):
    grads = grad_fn(m, b)         # 1. find downhill (gradient)
    dw, db = grads                # unpack: slope for w, slope for b

    m = m - learning_rate * dw    # 2. step m a little downhill
    b = b - learning_rate * db    # 2. step b a little downhill

    if step % 10 == 0:            # print every 10th step
        print(f"step {step:3d} | loss {loss_fn(m, b).item():.4f} | m {m.item():.3f} | b {b.item():.3f}")

print(f"\nFinal: m = {m.item():.3f}, b = {b.item():.3f}  (target was m=2, b=1)")
    # loss starts large and shrinks toward ~0 as it descends the hill.
    # m climbs from 0 to 2
    # b climbs from 0 to 1

# every neural network you ever train is this loop
    # what changes is weights
    # The manual w = w - lr * dw step gets handed to an optimizer (from mlx.optimizers) that does the nudging for you — but it's doing the same subtraction.
    # The data is images instead of five points.
