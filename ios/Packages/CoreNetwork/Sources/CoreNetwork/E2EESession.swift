import Foundation
import CryptoKit

public struct EncryptedEnvelope {
    public let iv: String
    public let ct: String
    public let aad: String
}

public class E2EESession {
    private let privateKey: Curve25519.KeyAgreement.PrivateKey
    public let publicKeyBase64: String
    
    private var c2sKey: SymmetricKey?
    private var s2cKey: SymmetricKey?
    private var msgCounter = 0
    
    public init() {
        self.privateKey = Curve25519.KeyAgreement.PrivateKey()
        self.publicKeyBase64 = privateKey.publicKey.rawRepresentation.base64EncodedString()
    }
    
    public func deriveSessionKeys(gatewayPubKeyBase64: String) throws {
        guard let pubKeyData = Data(base64Encoded: gatewayPubKeyBase64) else {
            throw E2EEError.invalidBase64
        }
        
        let gatewayPubKey = try Curve25519.KeyAgreement.PublicKey(rawRepresentation: pubKeyData)
        let sharedSecret = try privateKey.sharedSecretFromKeyAgreement(with: gatewayPubKey)
        
        // HKDF
        let c2sInfo = "antimatter-v1:client-to-server".data(using: .utf8)!
        let s2cInfo = "antimatter-v1:server-to-client".data(using: .utf8)!
        
        self.c2sKey = sharedSecret.hkdfDerivedSymmetricKey(
            using: SHA256.self,
            salt: Data(),
            sharedInfo: c2sInfo,
            outputByteCount: 32
        )
        
        self.s2cKey = sharedSecret.hkdfDerivedSymmetricKey(
            using: SHA256.self,
            salt: Data(),
            sharedInfo: s2cInfo,
            outputByteCount: 32
        )
    }
    
    public func encrypt(plaintext: String, direction: String = "cmd:") throws -> EncryptedEnvelope {
        guard let key = c2sKey else { throw E2EEError.keysNotDerived }
        
        msgCounter += 1
        let aadString = "\(direction)v1:msg_id:\(msgCounter)"
        let aad = aadString.data(using: .utf8)!
        
        let nonce = try AES.GCM.Nonce()
        let sealedBox = try AES.GCM.seal(plaintext.data(using: .utf8)!, using: key, nonce: nonce, authenticating: aad)
        
        // Python's AESGCM and Java's AES/GCM/NoPadding return Ciphertext + Tag concatenated.
        var ctData = Data(sealedBox.ciphertext)
        ctData.append(sealedBox.tag)
        
        let nonceBase64 = sealedBox.nonce.withUnsafeBytes { Data($0).base64EncodedString() }
        
        return EncryptedEnvelope(
            iv: nonceBase64,
            ct: ctData.base64EncodedString(),
            aad: aadString
        )
    }
    
    public func decrypt(ivB64: String, ctB64: String, aad: String, expectedDirection: String = "output:") throws -> String {
        guard let key = s2cKey else { throw E2EEError.keysNotDerived }
        guard aad.hasPrefix(expectedDirection) else { throw E2EEError.aadMismatch }
        
        guard let nonceData = Data(base64Encoded: ivB64),
              let ctAndTagData = Data(base64Encoded: ctB64) else {
            throw E2EEError.invalidBase64
        }
        
        let nonce = try AES.GCM.Nonce(data: nonceData)
        let aadData = aad.data(using: .utf8)!
        
        var combinedData = Data(nonceData)
        combinedData.append(ctAndTagData)
        
        let sealedBox = try AES.GCM.SealedBox(combined: combinedData)
        let decryptedData = try AES.GCM.open(sealedBox, using: key, authenticating: aadData)
        
        guard let plaintext = String(data: decryptedData, encoding: .utf8) else {
            throw E2EEError.decryptionFailed
        }
        
        return plaintext
    }
}

public enum E2EEError: Error {
    case invalidBase64
    case keysNotDerived
    case encryptionFailed
    case decryptionFailed
    case aadMismatch
}
