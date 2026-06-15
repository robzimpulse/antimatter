import SwiftUI
import CoreData
import CoreUI

public struct HistoryView: View {
    @Environment(\.managedObjectContext) private var viewContext
    
    @FetchRequest(
        entity: StepEntity.entity(),
        sortDescriptors: []
    ) private var steps: FetchedResults<StepEntity>
    
    @State private var searchText = ""
    @Environment(\.dismiss) private var dismiss
    
    public init() {}
    
    public var body: some View {
        NavigationStack {
            List {
                ForEach(steps) { step in
                    VStack(alignment: .leading) {
                        Text(step.text)
                            .lineLimit(2)
                            .font(.body)
                        Text("Conversation: \(step.conversationId)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            .searchable(text: $searchText, prompt: "Search offline history...")
            .onChange(of: searchText) { newValue in
                if newValue.isEmpty {
                    steps.nsPredicate = nil
                } else {
                    steps.nsPredicate = NSPredicate(format: "text CONTAINS[cd] %@", newValue)
                }
            }
            .navigationTitle("Chat History")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}
