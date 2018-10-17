"""
    DarkNet, implemented in TensorFlow.
    Original source: 'Darknet: Open source neural networks in c,' https://github.com/pjreddie/darknet.
"""

__all__ = ['darknet', 'darknet_ref', 'darknet_tiny', 'darknet19']

import os
import tensorflow as tf
from .common import conv2d, batchnorm, maxpool2d


def dark_conv(x,
              in_channels,
              out_channels,
              kernel_size,
              padding,
              training,
              name="dark_conv"):
    """
    DarkNet specific convolution block.

    Parameters:
    ----------
    x : Tensor
        Input tensor.
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    kernel_size : int or tuple/list of 2 int
        Convolution window size.
    padding : int or tuple/list of 2 int
        Padding value for convolution layer.
    training : bool, or a TensorFlow boolean scalar tensor, default False
      Whether to return the output in training mode or in inference mode.
    name : str, default 'dark_conv'
        Block name.

    Returns
    -------
    Tensor
        Resulted tensor.
    """
    x = conv2d(
        x=x,
        in_channels=in_channels,
        out_channels=out_channels,
        kernel_size=kernel_size,
        padding=padding,
        use_bias=False,
        name=name + "/conv")
    x = batchnorm(
        x=x,
        training=training,
        name=name + "/bn")
    x = tf.nn.leaky_relu(x, alpha=0.1, name=name + "/activ")
    return x


def dark_conv1x1(x,
                 in_channels,
                 out_channels,
                 training,
                 name="dark_conv1x1"):
    """
    1x1 version of the DarkNet specific convolution block.

    Parameters:
    ----------
    x : Tensor
        Input tensor.
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    training : bool, or a TensorFlow boolean scalar tensor, default False
      Whether to return the output in training mode or in inference mode.
    name : str, default 'dark_conv1x1'
        Block name.

    Returns
    -------
    Tensor
        Resulted tensor.
    """
    return dark_conv(
        x=x,
        in_channels=in_channels,
        out_channels=out_channels,
        kernel_size=1,
        padding=0,
        training=training,
        name=name)


def dark_conv3x3(x,
                 in_channels,
                 out_channels,
                 training,
                 name="dark_conv3x3"):
    """
    3x3 version of the DarkNet specific convolution block.

    Parameters:
    ----------
    x : Tensor
        Input tensor.
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    training : bool, or a TensorFlow boolean scalar tensor, default False
      Whether to return the output in training mode or in inference mode.
    name : str, default 'dark_conv3x3'
        Block name.

    Returns
    -------
    Tensor
        Resulted tensor.
    """
    return dark_conv(
        x=x,
        in_channels=in_channels,
        out_channels=out_channels,
        kernel_size=3,
        padding=1,
        training=training,
        name=name)


def dark_convYxY(x,
                 in_channels,
                 out_channels,
                 pointwise=True,
                 training=False,
                 name="dark_convYxY"):
    """
    DarkNet unit.

    Parameters:
    ----------
    x : Tensor
        Input tensor.
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    pointwise : bool
        Whether use 1x1 (pointwise) convolution or 3x3 convolution.
    training : bool, or a TensorFlow boolean scalar tensor, default False
      Whether to return the output in training mode or in inference mode.
    name : str, default 'dark_convYxY'
        Block name.

    Returns
    -------
    Tensor
        Resulted tensor.
    """
    if pointwise:
        return dark_conv1x1(
            x=x,
            in_channels=in_channels,
            out_channels=out_channels,
            training=training,
            name=name)
    else:
        return dark_conv3x3(
            x=x,
            in_channels=in_channels,
            out_channels=out_channels,
            training=training,
            name=name)


def darknet(x,
            channels,
            odd_pointwise,
            avg_pool_size,
            cls_activ,
            in_channels=3,
            classes=1000,
            training=False):
    """
    DarkNet model from 'Darknet: Open source neural networks in c,' https://github.com/pjreddie/darknet.

    Parameters:
    ----------
    x : Tensor
        Input tensor.
    channels : list of list of int
        Number of output channels for each unit.
    odd_pointwise : bool
        Whether pointwise convolution layer is used for each odd unit.
    avg_pool_size : int
        Window size of the final average pooling.
    cls_activ : bool
        Whether classification convolution layer uses an activation.
    in_channels : int, default 3
        Number of input channels.
    classes : int, default 1000
        Number of classification classes.
    training : bool, or a TensorFlow boolean scalar tensor, default False
      Whether to return the output in training mode or in inference mode.

    Returns
    -------
    Tensor
        Resulted tensor.
    """
    for i, channels_per_stage in enumerate(channels):
        for j, out_channels in enumerate(channels_per_stage):
            x = dark_convYxY(
                x=x,
                in_channels=in_channels,
                out_channels=out_channels,
                pointwise=(len(channels_per_stage) > 1) and not(((j + 1) % 2 == 1) ^ odd_pointwise),
                training=training,
                name="features/stage{}/unit{}".format(i + 1, j + 1))
            in_channels = out_channels
        if i != len(channels) - 1:
            x = maxpool2d(
                x=x,
                pool_size=2,
                strides=2,
                name="features/pool{}".format(i + 1))

    x = conv2d(
        x=x,
        in_channels=in_channels,
        out_channels=classes,
        kernel_size=1,
        name="output/final_conv")
    if cls_activ:
        x = tf.nn.leaky_relu(x, alpha=0.1, name="output/final_activ")
    x = tf.layers.average_pooling2d(
        inputs=x,
        pool_size=avg_pool_size,
        strides=1,
        data_format='channels_first',
        name="output/final_pool")
    x = tf.layers.flatten(x)

    return x


def get_darknet(version,
                model_name=None,
                pretrained=False,
                sess=None,
                root=os.path.join('~', '.tensorflow', 'models'),
                **kwargs):
    """
    Create DarkNet model with specific parameters.

    Parameters:
    ----------
    version : str
        Version of SqueezeNet ('ref', 'tiny' or '19').
    model_name : str or None, default None
        Model name for loading pretrained model.
    pretrained : bool, default False
        Whether to load the pretrained weights for model.
    sess: Session or None, default None
        A Session to use to load the weights.
    root : str, default '~/.tensorflow/models'
        Location for keeping the model parameters.
    """

    if version == 'ref':
        channels = [[16], [32], [64], [128], [256], [512], [1024]]
        odd_pointwise = False
        avg_pool_size = 3
        cls_activ = True
    elif version == 'tiny':
        channels = [[16], [32], [16, 128, 16, 128], [32, 256, 32, 256], [64, 512, 64, 512, 128]]
        odd_pointwise = True
        avg_pool_size = 14
        cls_activ = False
    elif version == '19':
        channels = [[32], [64], [128, 64, 128], [256, 128, 256], [512, 256, 512, 256, 512],
                    [1024, 512, 1024, 512, 1024]]
        odd_pointwise = False
        avg_pool_size = 7
        cls_activ = False
    # elif version == '53':
    #     init_block_channels = 32
    #     layers = [2, 8, 8, 4]
    #     channels_per_layers = [64, 128, 256, 512, 1024]
    #     channels = [[ci] * li for (ci, li) in zip(channels_per_layers, layers)]
    #     odd_pointwise = False
    #     avg_pool_size = 7
    #     cls_activ = False
    else:
        raise ValueError("Unsupported DarkNet version {}".format(version))

    if pretrained and ((model_name is None) or (not model_name)):
        raise ValueError("Parameter `model_name` should be properly initialized for loading pretrained model.")

    def net_lambda(x,
                   training=False,
                   channels=channels,
                   odd_pointwise=odd_pointwise,
                   avg_pool_size=avg_pool_size,
                   cls_activ=cls_activ,
                   pretrained=pretrained,
                   sess=sess,
                   model_name=model_name,
                   root=root):
        y_net = darknet(
            x=x,
            channels=channels,
            odd_pointwise=odd_pointwise,
            avg_pool_size=avg_pool_size,
            cls_activ=cls_activ,
            training=training,
            **kwargs)
        if pretrained:
            from .model_store import download_model
            download_model(
                sess=sess,
                model_name=model_name,
                local_model_store_dir_path=root)
        return y_net

    return net_lambda


def darknet_ref(**kwargs):
    """
    DarkNet 'Reference' model from 'Darknet: Open source neural networks in c,' https://github.com/pjreddie/darknet.

    Parameters:
    ----------
    pretrained : bool, default False
        Whether to load the pretrained weights for model.
    sess: Session or None, default None
        A Session to use to load the weights.
    root : str, default '~/.tensorflow/models'
        Location for keeping the model parameters.
    """
    return get_darknet(version="ref", model_name="darknet_ref", **kwargs)


def darknet_tiny(**kwargs):
    """
    DarkNet Tiny model from 'Darknet: Open source neural networks in c,' https://github.com/pjreddie/darknet.

    Parameters:
    ----------
    pretrained : bool, default False
        Whether to load the pretrained weights for model.
    sess: Session or None, default None
        A Session to use to load the weights.
    root : str, default '~/.tensorflow/models'
        Location for keeping the model parameters.
    """
    return get_darknet(version="tiny", model_name="darknet_tiny", **kwargs)


def darknet19(**kwargs):
    """
    DarkNet-19 model from 'Darknet: Open source neural networks in c,' https://github.com/pjreddie/darknet.

    Parameters:
    ----------
    pretrained : bool, default False
        Whether to load the pretrained weights for model.
    sess: Session or None, default None
        A Session to use to load the weights.
    root : str, default '~/.tensorflow/models'
        Location for keeping the model parameters.
    """
    return get_darknet(version="19", model_name="darknet19", **kwargs)


def _test():
    import numpy as np

    pretrained = False

    models = [
        darknet_ref,
        darknet_tiny,
        darknet19,
    ]

    for model in models:

        net = model(pretrained=pretrained)

        x = tf.placeholder(
            dtype=tf.float32,
            shape=(None, 3, 224, 224),
            name='xx')
        y_net = net(x)

        weight_count = np.sum([np.prod(v.get_shape().as_list()) for v in tf.trainable_variables()])
        print("m={}, {}".format(model.__name__, weight_count))
        assert (model != darknet_ref or weight_count == 7319416)
        assert (model != darknet_tiny or weight_count == 1042104)
        assert (model != darknet19 or weight_count == 20842376)

        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())
            x_value = np.zeros((1, 3, 224, 224), np.float32)
            y = sess.run(y_net, feed_dict={x: x_value})
            assert (y.shape == (1, 1000))
        tf.reset_default_graph()


if __name__ == "__main__":
    _test()
