// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "CoreNetwork",
    platforms: [.iOS(.v17)],
    products: [
        .library(
            name: "CoreNetwork",
            targets: ["CoreNetwork"]),
    ],
    dependencies: [

    ],
    targets: [
        .target(
            name: "CoreNetwork",
            dependencies: []),
        .testTarget(
            name: "CoreNetworkTests",
            dependencies: ["CoreNetwork"]),
    ]
)
