import glob
import os
import shutil
import sys

import pytest

import archetypal as ar


# Parametrization of the fixture scratch_then_cache. The following array
# tells pytest to use True than False for all tests that use this fixture.
# This is very usefull to test the behavior of methods that use cached data
# or not.
do = [True, False]


@pytest.fixture(params=do, ids=["from_scratch", "from_cache"], scope="function")
def scratch_then_cache(request):
    """# remove the tests/temp folder if it already exists so we
    start fresh with tests"""
    # request is a special parameter known to pytest. It passes whatever is in
    # params=do. Ids are there to give the test a human readable name.
    if request.param:
        dirs = [
            ar.settings.data_folder,
            ar.settings.cache_folder,
            ar.settings.imgs_folder,
        ]
        for dir in dirs:
            dir.rmtree_p()


samples_ = ["regular", "umi_samples"]  # ['problematic', 'regular',


# 'umi_samples']


@pytest.fixture(params=samples_, ids=samples_, scope="session")
def idf_source(request):
    return glob.glob("tests/input_data/{}/*.idf".format(request.param))


@pytest.fixture(scope="session")
def config():
    ar.config(
        data_folder="tests/.temp/data",
        logs_folder="tests/.temp/logs",
        imgs_folder="tests/.temp/images",
        cache_folder="tests/.temp/cache",
        use_cache=True,
        log_file=False,
        log_console=False,
        umitemplate="tests/input_data/umi_samples/BostonTemplateLibrary_2.json",
        debug=True,
    )


@pytest.fixture(scope="class")
def clean_config(config):
    """calls config fixture and clears default folders"""

    dirs = [ar.settings.data_folder, ar.settings.cache_folder, ar.settings.imgs_folder]
    for dir in dirs:
        dir.rmtree_p()


# List fixtures that are located outiside of conftest.py so that they can be
# used in other tests
pytest_plugins = ["tests.test_dataportals"]

ALL = set("darwin linux win32".split())


def pytest_runtest_setup(item):
    supported_platforms = ALL.intersection(mark.name for mark in item.iter_markers())
    plat = sys.platform
    if supported_platforms and plat not in supported_platforms:
        pytest.skip("cannot run on platform %s" % (plat))


# dynamically define files to be ignored
collect_ignore = ["test_core.py"]


def get_platform():
    """Returns the MacOS release number as tuple of ints"""
    import platform

    release, versioninfo, machine = platform.mac_ver()
    release_split = release.split(".")
    return tuple(map(safe_int_cast, release_split))


def safe_int_cast(val, default=0):
    """Safely casts a value to an int"""
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def no_duplicates(file, attribute="Name"):
    """

    Args:
        file (str): Path of the json file
        attribute (str): Attribute to search for duplicates in json UMI structure.
        eg. : "$id", "Name"

    Returns:

    """
    import json
    from collections import defaultdict

    if isinstance(file, str):
        data = json.loads(open(file).read())
    else:
        data = file
    ids = {}
    for key, value in data.items():
        ids[key] = defaultdict(int)
        for component in value:
            try:
                _id = component[attribute]
            except KeyError:
                pass  # BuildingTemplate does not have an id
            else:
                ids[key][_id] += 1
    dups = {
        key: dict(filter(lambda x: x[1] > 1, values.items()))
        for key, values in ids.items()
        if dict(filter(lambda x: x[1] > 1, values.items()))
    }
    if any(dups.values()):
        raise Exception(f"Duplicate {attribute} found: {dups}")
    else:
        return True
