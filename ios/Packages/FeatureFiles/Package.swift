// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "FeatureFiles",
    platforms: [.iOS(.v17)],
    products: [
        .library(
            name: "FeatureFiles",
            targets: ["FeatureFiles"]),
    ],
    dependencies: [
        .package(path: "../CoreNetwork"),
        .package(path: "../CoreUI")
    ],
    targets: [
        .target(
            name: "FeatureFiles",
            dependencies: ["CoreNetwork", "CoreUI"]),
        .testTarget(
            name: "FeatureFilesTests",
            dependencies: ["FeatureFiles"]),
    ]
)
