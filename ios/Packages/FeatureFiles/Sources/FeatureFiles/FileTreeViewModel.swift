import SwiftUI
import Observation
import CoreUI

public struct FileNode: Identifiable {
    public let id = UUID()
    public let name: String
    public let isDirectory: Bool
    public var children: [FileNode]?
    
    public init(name: String, isDirectory: Bool, children: [FileNode]? = nil) {
        self.name = name
        self.isDirectory = isDirectory
        self.children = children
    }
    
    // Recursive parser from JSON dicts
    public static func parseTree(_ jsonArray: [[String: Any]]) -> [FileNode] {
        return jsonArray.compactMap { dict in
            guard let name = dict["name"] as? String else { return nil }
            let isDir = (dict["isDirectory"] as? Bool) ?? false
            var parsedChildren: [FileNode]? = nil
            
            if let childrenArray = dict["children"] as? [[String: Any]] {
                parsedChildren = parseTree(childrenArray)
            }
            return FileNode(name: name, isDirectory: isDir, children: parsedChildren)
        }
    }
}

@Observable
public class FileTreeViewModel {
    public var rootFiles: [FileNode] = []
    public var allowedWorkspaces: [String] = []
    public var currentWorkspace: String? = nil
    
    public init() {
        NotificationCenter.default.addObserver(forName: Notification.Name("NewFileTree"), object: nil, queue: .main) { [weak self] notification in
            if let data = notification.object as? Data {
                do {
                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                       let treeArray = json["tree"] as? [[String: Any]] {
                        let parsedNodes = FileNode.parseTree(treeArray)
                        Task { @MainActor in
                            self?.rootFiles = parsedNodes
                        }
                    }
                } catch {
                    print("Error decoding File Tree: \(error)")
                }
            }
        }
        NotificationCenter.default.addObserver(forName: Notification.Name("NewAvailableAgents"), object: nil, queue: .main) { [weak self] notification in
            if let data = notification.object as? Data {
                do {
                    if let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] {
                        if let allowed = json["allowed_workspaces"] as? [String] {
                            Task { @MainActor in
                                self?.allowedWorkspaces = allowed
                            }
                        }
                        if let agents = json["agents"] as? [[String: Any]], let first = agents.first {
                            if let wsRoot = first["workspaceRoot"] as? String {
                                Task { @MainActor in
                                    self?.currentWorkspace = wsRoot
                                }
                            }
                        }
                    }
                } catch {
                    print("Error decoding AVAILABLE_AGENTS in FileTreeViewModel: \(error)")
                }
            }
        }
    }
    
    public func changeWorkspace(to newPath: String) {
        let payload = ["type": "CHANGE_WORKSPACE", "path": newPath]
        CoreNetwork.AgentProtocol.shared.sendMessage(payload)
        self.currentWorkspace = newPath
    }
}
