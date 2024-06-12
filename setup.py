# -*- coding: utf-8 -*-
import os
from setuptools import setup

packages = []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk("ab_online_admin"):
    # Ignore dirnames that start with '.'
    if "__init__.py" in filenames or "static" in dirpath or "templates" in dirpath:
        pkg = dirpath.replace(os.path.sep, ".")
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, ".")
        packages.append(pkg)

if "VERSION" in os.environ:
    version = os.environ["VERSION"]
else:
    version = os.environ.get("GIT_DESCRIBE_TAG", "0.0.0")

setup(
    name="ab-online-admin",
    version=version,
    packages=packages,
    include_package_data=True,
    author="Rémy Le Calloch",
    author_email="remy@lecalloch.net",
    license=open("LICENSE.txt").read(),
    install_requires=[],  # dependency management in conda recipe
    url="https://github.com/Pan6ora/ab-online-admin",
    long_description=open("README.md").read(),
    description="A web interface for Activity Browser Online",
    entry_points={
        "console_scripts": [
            "ab-online-admin = ab_online_admin:run_ab_online_admin",
        ]
    },
    package_dir={"": "."},
    package_data={
        "ab_online_admin": ["static/*",
                            "static/styles/*",
                            "templates/*"]
    },
)
