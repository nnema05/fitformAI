import mlx.core as mx
import numpy as np
from garment_model import GarmentNet
# the inference module, this is what app uses app uses and calls 

class_names = ["Pants", "Sweater", "Dress", "Shirt"]

# Load the trained model 
model = GarmentNet()
model.load_weights("garment_model.safetensors")
mx.eval(model.parameters())      # force the weights to actually load

def preprocess_one(pil_image):
    img = pil_image.convert("L").resize((28, 28))
    arr = (np.array(img, dtype=np.float32) / 255.0).flatten()
    return mx.array(arr)[None, :]      # add batch dim → shape (1, 784)

def predict(pil_image):
    x = preprocess_one(pil_image)
    logits = model(x)                       # raw scores, shape (1, 4)
    probs = mx.softmax(logits, axis=1)      # → probabilities that sum to 1
    idx = mx.argmax(probs, axis=1).item()   # best class index
    confidence = probs[0, idx].item()       # its probability
    return {"garment": class_names[idx], "confidence": round(confidence, 3)}

from datasets import load_dataset
ds = load_dataset("ashraq/fashion-product-images-small", split="train")
print(predict(ds[0]["image"]))     # should print something like {'garment': 'Shirt', 'confidence': 0.9}