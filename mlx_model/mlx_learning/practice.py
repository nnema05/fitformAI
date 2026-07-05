import mlx.core as mx

# create an array from python list
a = mx.array([1, 2, 3])
print(a)

#  a 2-row, 3-column grid of 0.0. The (2, 3) is the shape.
print(mx.zeros((2, 3)))
# same for 1s
print(mx.ones((2, 3)))

#numbers 0 through 9, like Python's range but as an array.
print(mx.arange(0, 10))

# a 2×3 grid of random numbers (this is how model weights start out — random).
print(mx.random.normal((2, 3)))

# inspecting shape, shape is SO important 
# the dimensions, e.g. (2, 3). Check this constantly.
print(a.shape)
    # [1, 2, 3] means (3,)
    # mx.array([1, 2, 3]) is one-dimensional. It's just a line of three numbers. 
    # It has no concept of "row" or "column" yet , those words only apply once you have two dimensions.
    # (3,) reads as: "one axis, and that axis has length 3." The trailing comma is Python's way of writing a one-element tuple — (3) is just the number 3 in parentheses, but (3,) is a tuple containing 3. 
    # MLX uses a tuple for shape even when there's only one axis, so you get (3,).
    # (1, 3) would mean two dimensions: 1 row, 3 columns — a genuine 2D grid that happens to be one row tall. That's a different object. To get it you'd need an extra set of brackets:
# the number type (e.g. float32, int32).
print(a.dtype) 
# how many dimensions (1D, 2D, 3D...).
print(a.ndim) 

a = mx.ones((2, 3))
b = mx.ones((2, 3))

# element wise math! operate on every nuber at at once!
print(a + b)  # add
print(a - b)  # subtract
print(a * b)  # multiply
print(a / b)  # divide
print(a*2)  # multiply by a scalar
# no loops needed, this is the point of arrays
    # understand vectorized means the operation hits the whole grid at once 
    # you almost never right loops over aray elemets in MLX
print(mx.sqrt(a))  # square root  
print(mx.exp(a))  # exponent   
print(mx.log(a))  # natural log

# reshaping - same numbers, diffrent grid 
print(a.reshape((3, 2)))  # reshape to 3 rows, 2 columns
print(a.flatten())  # flatten to 1D
print(a[None, :])  # add a new axis, making it 3D
print(mx.expand_dims(a, 0) ) #  add a new axis, making it 3D

a = mx.ones((2, 3))
b = mx.ones((3, 2))

# matrix multiplication, not element wise
print(a@b)  # matrix multiplication
# rule for a @ b: the number of columns in a must equal the number of rows in b. The result will have the same number of rows as a and the same number of columns as b.
    # (2,3) @ (3,4) → (2,4). If those inner numbers don't match, you get a shape error — get used to reading that error.

# aggregations!
print(mx.sum(a))  # sum of all elements
print(mx.mean(a))  # mean of all elements
print(mx.max(a))  # max of all elements 
print(mx.sum(a, axis=0)) # sum down columns, so sum along first axis, leaving the second axis (the columns) intact. The result is a 1D array with one number per column.
print(mx.sum(a, axis=1)) # sum across rows, so sum along second axis
# the axis column controls direction of the aggregation. axis=0 means "go down the rows, aggregating each column." axis=1 means "go across the columns, aggregating each row." The result is always one dimension smaller than the input.