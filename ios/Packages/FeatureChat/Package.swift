// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "FeatureChat",
    platforms: [.iOS(.v17)],
    products: [
        .library(
            name: "FeatureChat",
            targets: ["FeatureChat"]),
    ],
    dependencies: [
        .package(path: "../CoreNetwork"),
        .package(path: "../CoreData"),
        .package(path: "../CoreUI")
    ],
    targets: [
        .target(
            name: "FeatureChat",
            dependencies: ["CoreNetwork", "CoreData", "CoreUI"]),
        .testTarget(
            name: "FeatureChatTests",
            dependencies: ["FeatureChat"]),
    ]
)
