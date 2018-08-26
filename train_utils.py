import random

import chainer
import numpy as np
from chainer import training
from chainer.training import extensions

from func.compute_mean import compute_mean
from func.dataset_function import dataset_label
from func.resize import resize
from googlenetbn import GoogleNetBN


class PreprocessedDataset(chainer.dataset.DatasetMixin):

    def __init__(self, dataset_path, mean, crop_size, random=True):
        _, labels, fnames = dataset_label(dataset_path)
        self.base = chainer.datasets.LabeledImageDataset(list(zip(fnames, labels)))
        self.mean = mean
        self.crop_size = crop_size
        self.random = random

    def __len__(self):
        return len(self.base)

    def get_example(self, i):
        image, label = self.base[i]
        image = resize(image, self.crop_size)
        image = image - self.mean[:, None, None]
        image *= (1.0 / 255.0)  # Scale to [0,1]
        image = image.astype(np.float32)

        if self.random:
            if random.randint(0, 1):
                image = image[:, :, ::-1]

        return image, label


def train_run(train_data, epoch, batchsize,
               gpu, out, val_iteration, log_iteration, loaderjob,
              resume, pre_trainedmodel=True):

    b_names, labels, _ = dataset_label(train_data)
    model = GoogleNetBN(n_class=len(b_names))

    mean = compute_mean(dataset_path=train_data, insize=model.insize).mean(axis=(1, 2))
    model.mean = mean

    dataset = PreprocessedDataset(train_data, model.mean,  model.insize)
    train, val = chainer.datasets.split_dataset_random(dataset, int(len(dataset) * 0.8))

    if pre_trainedmodel:
        print("Load model")
        chainer.serializers.load_npz("tuned_googlenetbn.npz", model)

    if loaderjob <= 0:
        train_iter = chainer.iterators.SerialIterator(train, batchsize)
        val_iter = chainer.iterators.SerialIterator(val, batchsize, shuffle=False, repeat=False)

    else:
        train_iter = chainer.iterators.MultiprocessIterator(train,
                                                            batchsize,
                                                            n_processes=loaderjob)
        val_iter = chainer.iterators.MultiprocessIterator(val,
                                                          batchsize,
                                                          n_processes=loaderjob,
                                                          shuffle=False,
                                                          repeat=False)

    optimizer = chainer.optimizers.Adam()
    optimizer.setup(model)

    updater = training.StandardUpdater(train_iter, optimizer, device=gpu)
    trainer = training.Trainer(updater, (epoch, "epoch"), out)

    val_interval = (val_iteration, "iteration")
    log_interval = (log_iteration, "iteration")

    trainer.extend(extensions.Evaluator(val_iter, model, device=gpu), trigger=val_interval)

    trainer.extend(extensions.LogReport(trigger=log_interval))
    trainer.extend(extensions.observe_lr(), trigger=log_interval)
    trainer.extend(extensions.PrintReport(
        ['epoch',
         'iteration',
         'main/loss1',
         'main/loss2',
         'main/loss3',
         'main/loss',
         'main/accuracy',
         'validation/main/loss',
         'validation/main/accuracy',
         'elapsed_time',
         'lr']), trigger=log_interval)
    trainer.extend(extensions.ProgressBar(update_interval=10))
    trainer.extend(extensions.PlotReport(
        ["main/loss",
         "validation/main/loss"],
        x_key="epoch", file_name="loss.png"
    ))
    trainer.extend(extensions.PlotReport(
        ["main/accuracy",
         "validation/main/accuracy"],
        x_key="epoch", file_name="accuracy.png"))
    trainer.extend(extensions.snapshot(), trigger=val_interval)
    trainer.extend(extensions.snapshot_object(model, "model_epoch_{.updater.epoch}"),
                   trigger=(epoch, "epoch"))
    trainer.extend(extensions.dump_graph("main/loss"))

    if resume:
        chainer.serializers.load_npz(resume, trainer)

    trainer.run()






