import Foundation
import Observation

public struct Credentials: Codable {
    public var tunnelUrl: String
    public var pairingToken: String
    public var gatewayPubKey: String
    public var clientId: String?
    
    public init(tunnelUrl: String, pairingToken: String, gatewayPubKey: String, clientId: String? = nil) {
        self.tunnelUrl = tunnelUrl
        self.pairingToken = pairingToken
        self.gatewayPubKey = gatewayPubKey
        self.clientId = clientId
    }
}

@Observable
public class ConnectionStore {
    public static let shared = ConnectionStore()
    
    public var credentials: Credentials? {
        didSet {
            if let creds = credentials, let data = try? JSONEncoder().encode(creds) {
                try? KeychainManager.shared.save(key: "antimatter_credentials", data: data)
            } else if credentials == nil {
                KeychainManager.shared.delete(key: "antimatter_credentials")
            }
        }
    }
    
    public var hasCredentials: Bool {
        return credentials != nil
    }
    
    private init() {
        if let data = KeychainManager.shared.load(key: "antimatter_credentials"),
           let creds = try? JSONDecoder().decode(Credentials.self, from: data) {
            self.credentials = creds
        }
    }
    
    public func clearCredentials() {
        self.credentials = nil
    }
}
