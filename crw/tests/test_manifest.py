"""
Loads the plugin exactly the way the Dify runtime does.

A malformed tool YAML makes the plugin process exit(1) at startup, which Dify
surfaces to the user as an opaque "Runtime exited with error: exit status 1" on
their first tool call. This test is the cheapest way to catch that before ship.
"""

import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_plugin_registration_loads() -> None:
    from dify_plugin.config.config import DifyPluginEnv
    from dify_plugin.core.plugin_registration import PluginRegistration

    cwd = os.getcwd()
    os.chdir(PLUGIN_ROOT)
    sys.path.insert(0, PLUGIN_ROOT)
    try:
        registration = PluginRegistration(DifyPluginEnv())
    finally:
        os.chdir(cwd)
        sys.path.remove(PLUGIN_ROOT)

    _, provider_cls, tools = registration.tools_mapping["crw"]
    assert provider_cls.__name__ == "CrwProvider"
    assert set(tools) == {
        "scrape",
        "crawl",
        "crawl_status",
        "map",
        "search",
        "extract",
    }


def test_every_tool_declares_output_schema() -> None:
    """Without output_schema a workflow node exposes no typed variables, so a
    downstream node has to hand-write JSON paths against an untyped blob."""
    import yaml

    for path in sorted(os.listdir(os.path.join(PLUGIN_ROOT, "tools"))):
        if not path.endswith(".yaml"):
            continue
        with open(os.path.join(PLUGIN_ROOT, "tools", path)) as fh:
            spec = yaml.safe_load(fh)
        assert spec.get("output_schema", {}).get("properties"), path
