import SwiftUI
import FeatureConnect
import FeatureChat
import FeatureFiles
import CoreData
import CoreUI

import LocalAuthentication
import UserNotifications

@main
struct AntimatterApp: App {
    @State private var isUnlocked = false
    @State private var authError: String? = nil

    var body: some Scene {
        WindowGroup {
            if isUnlocked {
                AppCoordinator()
                    .environment(\.managedObjectContext, PersistenceController.shared.container.viewContext)
            } else {
                ZStack {
                    Color.black.edgesIgnoringSafeArea(.all)
                    VStack(spacing: 20) {
                        Image(systemName: "lock.fill")
                            .font(.system(size: 60))
                            .foregroundColor(.white)
                        Text("Antimatter Locked")
                            .font(.title)
                            .foregroundColor(.white)
                        
                        if let error = authError {
                            Text(error)
                                .foregroundColor(.red)
                                .multilineTextAlignment(.center)
                                .padding()
                        }
                        
                        Button(action: authenticate) {
                            Text("Authenticate to Unlock")
                                .padding()
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .cornerRadius(8)
                        }
                    }
                }
                .onAppear {
                    authenticate()
                    requestNotificationPermissions()
                }
            }
        }
    }

    func requestNotificationPermissions() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            if let error = error {
                print("Notification permission error: \(error)")
            }
        }
    }

    func authenticate() {
        let context = LAContext()
        var error: NSError?

        if context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) {
            let reason = "Unlock Antimatter to access local AI agents."

            context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: reason) { success, authenticationError in
                DispatchQueue.main.async {
                    if success {
                        self.isUnlocked = true
                    } else {
                        self.authError = authenticationError?.localizedDescription ?? "Failed to authenticate."
                    }
                }
            }
        } else {
            // Fallback: No biometrics, allow device passcode
            if context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &error) {
                context.evaluatePolicy(.deviceOwnerAuthentication, localizedReason: "Unlock Antimatter.") { success, authenticationError in
                    DispatchQueue.main.async {
                        if success {
                            self.isUnlocked = true
                        } else {
                            self.authError = authenticationError?.localizedDescription ?? "Failed to authenticate."
                        }
                    }
                }
            } else {
                // No passcode set, fail securely
                self.authError = "Device has no passcode or biometrics configured. Please secure your device."
            }
        }
    }
}
