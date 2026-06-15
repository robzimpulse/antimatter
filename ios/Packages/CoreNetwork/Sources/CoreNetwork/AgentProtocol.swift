import Foundation
import Observation
import CryptoKit
import UserNotifications

@Observable
public class AgentProtocol: NSObject, URLSessionWebSocketDelegate {
    public static let shared = AgentProtocol()
    
    private var webSocket: URLSessionWebSocketTask?
    public var isConnected = false
    public var currentTrajectory: [TrajectoryStep] = []
    
    private var e2eeSession: E2EESession?
    private var pendingChallenge: String?
    
    private override init() {
        super.init()
    }
    
    public func connect(credentials: Credentials) {
        guard let url = URL(string: credentials.tunnelUrl) else { return }
        
        var request = URLRequest(url: url)
        request.setValue("Bearer \(credentials.pairingToken)", forHTTPHeaderField: "Authorization")
        if let cid = credentials.clientId, !cid.isEmpty {
            request.setValue(cid, forHTTPHeaderField: "CF-Access-Client-Id")
        }
        
        let session = URLSession(configuration: .default, delegate: self, delegateQueue: OperationQueue())
        webSocket = session.webSocketTask(with: request)
        webSocket?.resume()
        
        // 1. Generate Auth Challenge immediately
        let challenge = UUID().uuidString
        self.pendingChallenge = challenge
        let authMsg = ["type": "AUTH_CHALLENGE", "challenge": challenge]
        sendPlaintextMessage(authMsg)
        
        schedulePing()
        receiveMessage()
    }
    
    public func disconnect() {
        webSocket?.cancel(with: .goingAway, reason: nil)
        isConnected = false
        e2eeSession = nil
        pendingChallenge = nil
    }
    
    private func schedulePing() {
        Task {
            try? await Task.sleep(nanoseconds: 15_000_000_000) // 15 seconds
            guard self.isConnected else { return }
            
            webSocket?.sendPing { error in
                if let error = error {
                    print("Ping failed: \(error)")
                    self.disconnect()
                } else {
                    self.schedulePing()
                }
            }
        }
    }
    
    private func receiveMessage() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .failure(let error):
                print("WebSocket error: \(error)")
                self?.isConnected = false
            case .success(let message):
                switch message {
                case .string(let text):
                    self?.handleIncomingText(text)
                case .data(let data):
                    print("Received binary data: \(data)")
                @unknown default:
                    break
                }
                // Keep listening
                self?.receiveMessage()
            }
        }
    }
    
    private func sendPlaintextMessage(_ payload: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: payload),
              let jsonString = String(data: data, encoding: .utf8) else { return }
        
        webSocket?.send(.string(jsonString)) { error in
            if let error = error {
                print("Failed to send plaintext message: \(error)")
            }
        }
    }
    
    public func sendMessage(_ payload: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: payload),
              let jsonString = String(data: data, encoding: .utf8) else { return }
        
        guard let e2ee = e2eeSession else {
            print("Cannot send message, E2EE not established.")
            return
        }
        
        do {
            let encrypted = try e2ee.encrypt(plaintext: jsonString, direction: "cmd:")
            let wireMsg = [
                "iv": encrypted.iv,
                "ct": encrypted.ct,
                "aad": encrypted.aad
            ]
            sendPlaintextMessage(wireMsg)
        } catch {
            print("Encryption failed: \(error)")
        }
    }
    
    private func handleIncomingText(_ text: String) {
        guard let data = text.data(using: .utf8) else { return }
        
        do {
            if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] {
                // 1. Is it an encrypted payload?
                if let iv = json["iv"] as? String,
                   let ct = json["ct"] as? String,
                   let aad = json["aad"] as? String {
                    
                    guard let e2ee = e2eeSession else {
                        print("Received encrypted payload but E2EE is not initialized.")
                        return
                    }
                    
                    let plaintext = try e2ee.decrypt(ivB64: iv, ctB64: ct, aad: aad, expectedDirection: "output:")
                    if let plainData = plaintext.data(using: .utf8),
                       let plainJson = try JSONSerialization.jsonObject(with: plainData, options: []) as? [String: Any],
                       let type = plainJson["type"] as? String {
                        handleDecryptedPayload(type: type, data: plainData, json: plainJson)
                    }
                    return
                }
                
                // 2. Is it a plaintext protocol message? (e.g. AUTH_RESPONSE)
                if let type = json["type"] as? String {
                    if type == "AUTH_RESPONSE" {
                        handleAuthResponse(json: json)
                        return
                    } else if type == "ERROR" {
                        print("Gateway Error: \(json["message"] as? String ?? "")")
                        return
                    }
                }
                
                // 3. Fallback (legacy plaintext, should not happen in E2EE mode)
                print("Warning: Received unencrypted plaintext: \(text)")
            }
        } catch {
            print("Failed to parse incoming message: \(error)")
        }
    }
    
    private func handleAuthResponse(json: [String: Any]) {
        guard let signatureB64 = json["signature"] as? String,
              let challenge = pendingChallenge,
              let credentials = ConnectionStore.shared.credentials else {
            print("Invalid AUTH_RESPONSE or missing local state")
            self.disconnect()
            return
        }
        
        do {
            // Reconstruct Ed25519 Public Key
            guard let sigData = Data(base64Encoded: signatureB64),
                  let pubKeyData = Data(base64Encoded: credentials.pairingToken) else {
                throw E2EEError.invalidBase64
            }
            
            let pubKey = try Curve25519.Signing.PublicKey(rawRepresentation: pubKeyData)
            let challengeData = challenge.data(using: .utf8)!
            
            if pubKey.isValidSignature(sigData, for: challengeData) {
                print("Ed25519 Handshake Verified. Initializing E2EE.")
                let e2ee = E2EESession()
                try e2ee.deriveSessionKeys(gatewayPubKeyBase64: credentials.gatewayPubKey)
                self.e2eeSession = e2ee
                
                let helloMsg = ["type": "HELLO", "pubkey": e2ee.publicKeyBase64]
                sendPlaintextMessage(helloMsg)
                print("Sent HELLO X25519 payload. E2EE Established.")
                
                Task { @MainActor in
                    self.isConnected = true
                }
            } else {
                print("Ed25519 Signature INVALID. Aborting connection.")
                self.disconnect()
            }
        } catch {
            print("Crypto Error during Auth: \(error)")
            self.disconnect()
        }
    }
    
    private func handleDecryptedPayload(type: String, data: Data, json: [String: Any]) {
        do {
            switch type {
            case "STEP":
                let step = try JSONDecoder().decode(TrajectoryStep.self, from: data)
                Task { @MainActor in
                    self.currentTrajectory.append(step)
                }
            case "STEP_BATCH":
                if let stepsDict = json["steps"] as? [[String: Any]] {
                    let stepsData = try JSONSerialization.data(withJSONObject: stepsDict)
                    let newSteps = try JSONDecoder().decode([TrajectoryStep].self, from: stepsData)
                    Task { @MainActor in
                        self.currentTrajectory.append(contentsOf: newSteps)
                    }
                }

            case "FILE_TREE":
                NotificationCenter.default.post(name: Notification.Name("NewFileTree"), object: data)
            case "FILE_CONTENT":
                NotificationCenter.default.post(name: Notification.Name("NewFileContent"), object: data)
            case "AVAILABLE_AGENTS":
                NotificationCenter.default.post(name: Notification.Name("NewAvailableAgents"), object: data)
            case "SYSTEM_NOTIFICATION":
                if let title = json["title"] as? String, let body = json["body"] as? String {
                    let content = UNMutableNotificationContent()
                    content.title = title
                    content.body = body
                    content.sound = .default
                    let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil)
                    UNUserNotificationCenter.current().add(request)
                }
            default:
                break
            }
        } catch {
            print("Failed to decode decrypted payload: \(error)")
        }
    }
    
    public func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        // Wait for E2EE handshake before setting isConnected = true
        print("WebSocket opened. Awaiting Auth Response...")
    }
    
    public func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        Task { @MainActor in
            self.isConnected = false
            self.e2eeSession = nil
        }
    }
}
