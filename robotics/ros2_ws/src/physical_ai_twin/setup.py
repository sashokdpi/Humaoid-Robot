from setuptools import setup

package_name = "physical_ai_twin"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Physical AI",
    maintainer_email="dev@physical.ai",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "twin_validate_node = physical_ai_twin.twin_validate_node:main",
        ],
    },
)
