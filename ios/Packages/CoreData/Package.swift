// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "CoreData",
    platforms: [.iOS(.v17)],
    products: [
        .library(
            name: "CoreData",
            targets: ["CoreData"]),
    ],
    dependencies: [

    ],
    targets: [
        .target(
            name: "CoreData",
            dependencies: []),
        .testTarget(
            name: "CoreDataTests",
            dependencies: ["CoreData"]),
    ]
)
