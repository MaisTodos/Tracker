import types
from huble.integrations import attach_framework

class _Hit:
    called = False
    args = None
    kwargs = None
    @classmethod
    def reset(cls):
        cls.called, cls.args, cls.kwargs = False, None, None
    @classmethod
    def attach(cls, app, **kwargs):
        cls.called = True
        cls.args, cls.kwargs = (app,), kwargs

def test_dispatch_fastapi(monkeypatch):
    from sys import modules
    mod = types.ModuleType("huble.integrations.fastapi_fw")
    class FakeAdapter:
        def attach(self, app, **kwargs):
            _Hit.attach(app, **kwargs)
    mod.HubleFrameworkAdapter = FakeAdapter
    monkeypatch.setitem(modules, "huble.integrations.fastapi_fw", mod)

    class FakeFastAPI:
        router = object()
    _Hit.reset()
    attach_framework(FakeFastAPI(), log_request_response=True)
    assert _Hit.called is True
    assert _Hit.kwargs.get("log_request_response") is True

def test_dispatch_django(monkeypatch):
    from sys import modules
    mod = types.ModuleType("huble.integrations.django_fw")
    class FakeAdapter:
        def attach(self, app, **kwargs):
            _Hit.attach(app, **kwargs)
    mod.HubleFrameworkAdapter = FakeAdapter
    monkeypatch.setitem(modules, "huble.integrations.django_fw", mod)

    class FakeDjangoApp:
        _is_django = True
    _Hit.reset()
    attach_framework(FakeDjangoApp(), log_request_response=False)
    assert _Hit.called is True

def test_dispatch_chalice(monkeypatch):
    from sys import modules
    mod = types.ModuleType("huble.integrations.chalice_fw")
    class FakeAdapter:
        def attach(self, app, **kwargs):
            _Hit.attach(app, **kwargs)
    mod.HubleFrameworkAdapter = FakeAdapter
    monkeypatch.setitem(modules, "huble.integrations.chalice_fw", mod)

    class FakeChalice:
        app_name = "demo"
    _Hit.reset()
    attach_framework(FakeChalice(), some_flag=123)
    assert _Hit.called is True
    assert _Hit.kwargs.get("some_flag") == 123
