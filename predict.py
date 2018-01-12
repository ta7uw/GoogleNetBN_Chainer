import argparse

import chainer
import numpy as np
from PIL import Image

from func.compute_mean import compute_mean
from func.dataset_function import dataset_label
from func.resize import resize
from googlenetbn import GoogleNetBN


def predict():
    parser = argparse.ArgumentParser(description="Predict item of image file ")
    parser.add_argument("--dataset", default="dataset")
    parser.add_argument("pretrained_model")
    parser.add_argument("image")
    args = parser.parse_args()

    # Get the label data used for training.
    # It use for getting number of class when predicting
    b_names, _, label_name = dataset_label(args.dataset)

    model = GoogleNetBN(n_class=len(b_names))
    chainer.serializers.load_npz(args.pretrained_model, model)
    mean = compute_mean(dataset_path=args.dataset, insize=model.insize).mean(axis=(1, 2))
    image = args.image
    image = Image.open(image)
    image = np.asarray(image, dtype=np.float32)
    image = image.transpose(2, 0, 1)
    image = resize(image, model.insize)
    image = image - mean[:, None, None]
    image = image.astype(np.float32)
    image *= (1.0 / 255.0)  # Scale to [0,1]
    image = image[np.newaxis, :]

    chainer.config.train = False
    y = model.predict(image)
    y = y.data[0]

    pred = b_names[int(y.argmax())]
    score = y.max()

    print("pred:", pred)
    print("score:", score)

if __name__ == '__main__':
    predict()