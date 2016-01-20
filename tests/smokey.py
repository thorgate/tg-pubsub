def test_imports():
    """ Ensures all submodules are importable
    Acts as a simple smoketest.
    """
    import tg_pubsub

    from tg_pubsub import config
    from tg_pubsub import exceptions
    from tg_pubsub import messages
    from tg_pubsub import models
    from tg_pubsub import protocol
    from tg_pubsub import pubsub
    from tg_pubsub import worker

    from tg_pubsub.management.commands.control_server import Command

    assert config.extra_models == {}
    assert config.extra_models == config.get_extra_models()
