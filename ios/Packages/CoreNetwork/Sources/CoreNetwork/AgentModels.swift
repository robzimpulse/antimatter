import Foundation
import CoreData

public struct AgentStep: Codable {
    public let `case`: String
    public let value: String?
    public let tool: String?
}

public struct TrajectoryStep: Codable, Identifiable {
    public let id: Int
    public let step: AgentStep
    
    // Computed properties for the UI to bind to
    public var type: String { return step.`case` }
    public var content: String? { return step.value }
    public var source: String { 
        return (step.`case` == "userInput") ? "USER" : "MODEL" 
    }
    
    enum CodingKeys: String, CodingKey {
        case id = "index"
        case step
    }
}

public struct AgentMessage: Codable {
    public let type: String
    public let payload: String
}
