// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "CoreUI",
    platforms: [.iOS(.v17)],
    products: [
        .library(
            name: "CoreUI",
            targets: ["CoreUI"]),
    ],
    dependencies: [

    ],
    targets: [
        .target(
            name: "CoreUI",
            dependencies: []),
        .testTarget(
            name: "CoreUITests",
            dependencies: ["CoreUI"]),
    ]
)
