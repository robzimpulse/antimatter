import SwiftUI
import Observation
import CoreData
import CoreNetwork
import CoreUI

@Observable
public class ConnectViewModel {
    public var inputToken: String = ""
    public var isConnecting: Bool = false
    public var errorMessage: String?
    public var showScanner: Bool = false
    
    public init() {}
    
    public func handleScannedCode(_ code: String) {
        showScanner = false
        inputToken = code
        connect()
    }
    
    public func connect() {
        guard !inputToken.isEmpty else {
            errorMessage = "Please enter a connection URL or pairing token."
            return
        }
        
        isConnecting = true
        errorMessage = nil
        
        // Parse Deep Link URL or fallback to raw token
        var tunnelUrl = "wss://antimatter-bridge.cloudflare.net"
        var token = inputToken
        var pubKey = ""
        var clientId: String? = nil
        
        if let url = URL(string: inputToken), let components = URLComponents(url: url, resolvingAgainstBaseURL: false) {
            if let queryItems = components.queryItems {
                if let tUrl = queryItems.first(where: { $0.name == "url" })?.value {
                    tunnelUrl = tUrl
                }
                if let tToken = queryItems.first(where: { $0.name == "token" })?.value {
                    token = tToken
                }
                if let tPub = queryItems.first(where: { $0.name == "x25519_pub" })?.value {
                    pubKey = tPub
                }
                clientId = queryItems.first(where: { $0.name == "cid" })?.value
            }
        } else {
            // Legacy/raw token format, missing E2EE pubkey. Will fail E2EE handshake but we pass it anyway.
            token = inputToken
        }
        
        // Ensure wss:// prefix
        if tunnelUrl.starts(with: "http://") {
            tunnelUrl = tunnelUrl.replacingOccurrences(of: "http://", with: "ws://")
        } else if tunnelUrl.starts(with: "https://") {
            tunnelUrl = tunnelUrl.replacingOccurrences(of: "https://", with: "wss://")
        }
        
        let creds = Credentials(tunnelUrl: tunnelUrl, pairingToken: token, gatewayPubKey: pubKey, clientId: clientId)
        ConnectionStore.shared.credentials = creds
        
        // Start connection on AgentProtocol
        AgentProtocol.shared.connect(credentials: creds)
        
        // Timeout check for handshake
        Task {
            try? await Task.sleep(nanoseconds: 5_000_000_000) // 5 seconds
            if !AgentProtocol.shared.isConnected {
                await MainActor.run {
                    self.isConnecting = false
                    self.errorMessage = "Failed to connect or authenticate with local agent daemon."
                    ConnectionStore.shared.clearCredentials()
                }
            }
        }
    }
}
