import SwiftUI
import CoreUI

public struct ConnectView: View {
    @Bindable var viewModel: ConnectViewModel
    
    public init(viewModel: ConnectViewModel = ConnectViewModel()) {
        self.viewModel = viewModel
    }
    
    public var body: some View {
        ZStack {
            AntimatterTheme.background.ignoresSafeArea()
            
            VStack(spacing: 32) {
                Spacer()
                
                // Logo placeholder
                Circle()
                    .fill(AntimatterTheme.primary.opacity(0.1))
                    .frame(width: 120, height: 120)
                    .overlay(
                        Image(systemName: "atom")
                            .font(.system(size: 60))
                            .foregroundColor(AntimatterTheme.primary)
                    )
                
                VStack(spacing: 8) {
                    Text("Antimatter")
                        .font(.system(.largeTitle, design: .rounded).bold())
                        .foregroundColor(AntimatterTheme.textPrimary)
                    
                    Text("Scan the QR code or enter your connection URL.")
                        .font(.subheadline)
                        .foregroundColor(AntimatterTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
                
                VStack(spacing: 16) {
                    HStack {
                        TextField("Connection URL", text: $viewModel.inputToken)
                            .padding()
                            .background(AntimatterTheme.secondary)
                            .cornerRadius(12)
                            .foregroundColor(AntimatterTheme.textPrimary)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                        
                        Button(action: {
                            viewModel.showScanner = true
                        }) {
                            Image(systemName: "qrcode.viewfinder")
                                .font(.title2)
                                .padding()
                                .background(AntimatterTheme.secondary)
                                .cornerRadius(12)
                                .foregroundColor(AntimatterTheme.primary)
                        }
                    }
                    
                    if let error = viewModel.errorMessage {
                        Text(error)
                            .foregroundColor(AntimatterTheme.error)
                            .font(.caption)
                    }
                    
                    Button(action: {
                        viewModel.connect()
                    }) {
                        if viewModel.isConnecting {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: AntimatterTheme.background))
                        } else {
                            Text("Connect")
                                .bold()
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(AntimatterTheme.primary)
                    .foregroundColor(AntimatterTheme.background)
                    .cornerRadius(12)
                    .disabled(viewModel.inputToken.isEmpty || viewModel.isConnecting)
                }
                .padding(.horizontal, 24)
                
                Spacer()
            }
        }
        .sheet(isPresented: $viewModel.showScanner) {
            ZStack(alignment: .topTrailing) {
                QRScannerView { code in
                    viewModel.handleScannedCode(code)
                }
                .ignoresSafeArea()
                
                Button(action: {
                    viewModel.showScanner = false
                }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.largeTitle)
                        .foregroundColor(.white)
                        .padding()
                }
            }
        }
    }
}

#Preview {
    ConnectView()
}
