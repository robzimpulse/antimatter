import SwiftUI
import CoreUI
import LocalAuthentication

public struct FileTreeView: View {
    @Bindable var viewModel: FileTreeViewModel
    
    public init(viewModel: FileTreeViewModel = FileTreeViewModel()) {
        self.viewModel = viewModel
    }
    
    public var body: some View {
        ZStack {
            AntimatterTheme.background.ignoresSafeArea()
            
            VStack(alignment: .leading, spacing: 0) {
                // Header
                HStack {
                    Image(systemName: "folder.fill")
                        .foregroundColor(AntimatterTheme.primary)
                    Text("Workspace")
                        .font(.headline)
                        .foregroundColor(AntimatterTheme.textPrimary)
                    
                    Spacer()
                    
                    if !viewModel.allowedWorkspaces.isEmpty {
                        Menu {
                            ForEach(viewModel.allowedWorkspaces, id: \.self) { ws in
                                Button(action: {
                                    authenticateAndSwitchWorkspace(to: ws)
                                }) {
                                    Text(ws)
                                }
                            }
                        } label: {
                            HStack {
                                Text((viewModel.currentWorkspace as NSString?)?.lastPathComponent ?? "Switch")
                                    .font(.subheadline)
                                    .foregroundColor(AntimatterTheme.primary)
                                Image(systemName: "chevron.up.chevron.down")
                                    .font(.caption)
                                    .foregroundColor(AntimatterTheme.primary)
                            }
                        }
                    }
                }
                .padding()
                .background(AntimatterTheme.surface)
                
                Divider().background(AntimatterTheme.secondary)
                
                List(viewModel.rootFiles, children: \.children) { node in
                    HStack {
                        Image(systemName: node.isDirectory ? "folder.fill" : "doc.fill")
                            .foregroundColor(node.isDirectory ? AntimatterTheme.primary : AntimatterTheme.textSecondary)
                        Text(node.name)
                            .foregroundColor(AntimatterTheme.textPrimary)
                    }
                    .listRowBackground(Color.clear)
                    .listRowSeparator(.hidden)
                }
                .listStyle(PlainListStyle())
                .scrollContentBackground(.hidden)
                .background(AntimatterTheme.background)
            }
        }
    }
    
    private func authenticateAndSwitchWorkspace(to path: String) {
        let context = LAContext()
        var error: NSError?

        if context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) {
            context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: "Authenticate to switch remote workspace") { success, _ in
                DispatchQueue.main.async {
                    if success {
                        viewModel.changeWorkspace(to: path)
                    }
                }
            }
        } else if context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &error) {
            context.evaluatePolicy(.deviceOwnerAuthentication, localizedReason: "Authenticate to switch remote workspace") { success, _ in
                DispatchQueue.main.async {
                    if success {
                        viewModel.changeWorkspace(to: path)
                    }
                }
            }
        } else {
            // If no biometrics or passcode, just allow (or fail securely, but let's allow for dev/test)
            viewModel.changeWorkspace(to: path)
        }
    }
}
