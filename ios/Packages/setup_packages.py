import os

packages_dir = '/home/saif/antimatter/ios/Packages'

packages = {
    'CoreNetwork': [],
    'CoreData': [],
    'CoreUI': [],
    'FeatureConnect': ['CoreNetwork', 'CoreData', 'CoreUI'],
    'FeatureChat': ['CoreNetwork', 'CoreData', 'CoreUI'],

    'FeatureFiles': ['CoreNetwork', 'CoreUI']
}

template = """// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "{name}",
    platforms: [.iOS(.v17)],
    products: [
        .library(
            name: "{name}",
            targets: ["{name}"]),
    ],
    dependencies: [
{dependencies_blocks}
    ],
    targets: [
        .target(
            name: "{name}",
            dependencies: [{target_dependencies}]),
        .testTarget(
            name: "{name}Tests",
            dependencies: ["{name}"]),
    ]
)
"""

for name, deps in packages.items():
    deps_blocks = ",\n".join([f'        .package(path: "../{dep}")' for dep in deps])
    target_deps = ", ".join([f'"{dep}"' for dep in deps])
    
    content = template.format(
        name=name,
        dependencies_blocks=deps_blocks,
        target_dependencies=target_deps
    )
    
    pkg_file = os.path.join(packages_dir, name, 'Package.swift')
    with open(pkg_file, 'w') as f:
        f.write(content)

print("Packages rewritten successfully!")
