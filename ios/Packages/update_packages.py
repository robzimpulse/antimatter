import os
import glob

packages_dir = '/home/saif/antimatter/ios/Packages'

deps_map = {
    'FeatureChat': ['CoreNetwork', 'CoreData', 'CoreUI'],
    'FeatureConnect': ['CoreNetwork', 'CoreData', 'CoreUI'],

    'FeatureFiles': ['CoreNetwork', 'CoreUI'],
    'CoreNetwork': [],
    'CoreData': [],
    'CoreUI': []
}

for package in deps_map.keys():
    pkg_file = os.path.join(packages_dir, package, 'Package.swift')
    with open(pkg_file, 'r') as f:
        content = f.read()

    # Add platforms: [.iOS(.v17)]
    if 'platforms' not in content:
        content = content.replace('name: "%s",' % package, 'name: "%s",\n    platforms: [.iOS(.v17)],' % package)

    # Add dependencies
    deps_blocks = []
    target_deps = []
    for dep in deps_map[package]:
        deps_blocks.append(f'.package(path: "../{dep}")')
        target_deps.append(f'"{dep}"')

    if deps_blocks:
        deps_str = ',\n        '.join(deps_blocks)
        content = content.replace('dependencies: [', f'dependencies: [\n        {deps_str}')
        
        target_deps_str = ', '.join(target_deps)
        content = content.replace('dependencies: [', f'dependencies: [{target_deps_str}, ', 1) # Note: this is crude, better to replace the target deps specifically.
        
    with open(pkg_file, 'w') as f:
        f.write(content)

print("Updated Packages!")
