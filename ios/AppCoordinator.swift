import SwiftUI
import Observation
import FeatureConnect
import FeatureChat
import FeatureFiles
import CoreData
import CoreUI

public struct AppCoordinator: View {
    @Bindable var tokenStore = TokenStore.shared
    @State private var selectedTab = 0
    
    public init() {}
    
    public var body: some View {
        Group {
            if tokenStore.hasToken {
                // Main App Experience
                TabView(selection: $selectedTab) {
                    ChatView()
                        .tabItem {
                            Label("Chat", systemImage: "bubble.left.and.bubble.right.fill")
                        }
                        .tag(0)
                    

                    
                    FileTreeView()
                        .tabItem {
                            Label("Files", systemImage: "folder.fill")
                        }
                        .tag(2)
                }
                .tint(AntimatterTheme.primary)
                .onAppear {
                    // Customize TabBar appearance for dark theme
                    let appearance = UITabBarAppearance()
                    appearance.configureWithOpaqueBackground()
                    appearance.backgroundColor = UIColor(AntimatterTheme.surface)
                    UITabBar.appearance().standardAppearance = appearance
                    UITabBar.appearance().scrollEdgeAppearance = appearance
                }
            } else {
                // Login / Pairing Screen
                ConnectView()
            }
        }
        .preferredColorScheme(.dark) // Force dark mode matching Android theme
    }
}
