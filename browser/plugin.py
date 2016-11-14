from __future__ import print_function
import pytest

from browser.test_browser import TestBrowser


def pytest_addoption(parser):
    parser.addoption("--browse", "--br", action="store_true",
                     dest='browse',
                     help="enable browser selection of tests after"
                     " collection using a console browser")


@pytest.mark.trylast
def pytest_collection_modifyitems(session, config, items):
    """called after collection has been performed, may filter or re-order
    the items in-place.
    """
    if not (config.option.browse and items):
        return

    capture_manager = config.pluginmanager.getplugin("capturemanager")
    if capture_manager:
        capture_manager.suspendcapture(in_=True)

    test_browser = TestBrowser(items=items)
    test_browser.main()
    items[:] = test_browser.get_selected_items()

    # TODO: Figure out some way out printing this to the console before the test run.
    # print("Selected %d items", len(items))

    if capture_manager:
        capture_manager.suspendcapture(in_=False)
