import os
from glob import glob
from setuptools import setup

package_name = "dexter_inventory"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
        (
            os.path.join("share", package_name, "templates"),
            glob(os.path.join("templates", "*.html")),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Your Name",
    maintainer_email="you@example.com",
    description="FEFO/FIFO inventory system for Dexter arm with RFID simulation and RL optimization",
    license="Apache 2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "inventory_node = dexter_inventory.inventory_node:main",
            "seed_data      = dexter_inventory.seed_data:seed",
            "standalone_dashboard = dexter_inventory.standalone_dashboard:app.run",
            "aruco_box_detector = dexter_inventory.aruco_box_detector:main",
        ],
    },
)
