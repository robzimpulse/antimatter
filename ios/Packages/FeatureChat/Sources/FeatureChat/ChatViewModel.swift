import SwiftUI
import Observation
import CoreNetwork
import CoreData
import UIKit

@Observable
public class ChatViewModel {
    public var inputText: String = ""
    public var showHistory: Bool = false
    public var selectedImageData: Data? = nil
    
    public var trajectories: [TrajectoryStep] {
        return AgentProtocol.shared.currentTrajectory
    }
    
    public init() {}
    
    public func connectToAgent() {
        if let token = TokenStore.shared.pairingToken {
            AgentProtocol.shared.connect(token: token)
        }
    }
    
    public func sendMessage() {
        if inputText.isEmpty && selectedImageData == nil { return }
        
        let textToSend = inputText.isEmpty ? "Attached an image." : inputText
        
        var payload: [String: Any] = [
            "type": "SEND_MESSAGE",
            "content": textToSend
        ]
        
        if let data = selectedImageData, let uiImage = UIImage(data: data) {
            // Resize image to max 1024x1024
            let maxDim: CGFloat = 1024
            let scale = min(maxDim/uiImage.size.width, maxDim/uiImage.size.height)
            let newImage: UIImage
            
            if scale < 1.0 {
                let newSize = CGSize(width: uiImage.size.width * scale, height: uiImage.size.height * scale)
                UIGraphicsBeginImageContextWithOptions(newSize, false, 1.0)
                uiImage.draw(in: CGRect(origin: .zero, size: newSize))
                newImage = UIGraphicsGetImageFromCurrentImageContext() ?? uiImage
                UIGraphicsEndImageContext()
            } else {
                newImage = uiImage
            }
            
            // Compress and convert to base64
            if let jpegData = newImage.jpegData(compressionQuality: 0.7) {
                let base64 = jpegData.base64EncodedString()
                let dataUri = "data:image/jpeg;base64,\(base64)"
                payload["images"] = [dataUri]
            }
        }
        
        AgentProtocol.shared.sendMessage(payload)
        
        inputText = ""
        selectedImageData = nil
    }
    
    public func disconnect() {
        AgentProtocol.shared.disconnect()
        TokenStore.shared.clearToken()
    }
}
