import SwiftUI

public enum AntimatterTheme {
    // We are implementing the Android-parity Dark Theme
    public static let background = Color(hex: "#09090B") // Extremely dark gray/black
    public static let surface = Color(hex: "#18181B") // Slightly lighter surface
    public static let primary = Color(hex: "#00E5FF") // Cyan/Neon Blue from the Antimatter logo
    public static let secondary = Color(hex: "#3F3F46") // Secondary surface/border
    public static let textPrimary = Color.white
    public static let textSecondary = Color(hex: "#A1A1AA")
    public static let error = Color.red
}

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
