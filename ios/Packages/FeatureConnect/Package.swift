// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "FeatureConnect",
    platforms: [.iOS(.v17)],
    products: [
        .library(
            name: "FeatureConnect",
            targets: ["FeatureConnect"]),
    ],
    dependencies: [
        .package(path: "../CoreNetwork"),
        .package(path: "../CoreData"),
        .package(path: "../CoreUI")
    ],
    targets: [
        .target(
            name: "FeatureConnect",
            dependencies: ["CoreNetwork", "CoreData", "CoreUI"]),
        .testTarget(
            name: "FeatureConnectTests",
            dependencies: ["FeatureConnect"]),
    ]
)
