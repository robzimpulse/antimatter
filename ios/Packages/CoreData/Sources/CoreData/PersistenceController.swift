import Foundation
import CoreData

public class PersistenceController {
    public static let shared = PersistenceController()

    public let container: NSPersistentContainer

    private init(inMemory: Bool = false) {
        let model = NSManagedObjectModel()
        
        let conversationEntity = NSEntityDescription()
        conversationEntity.name = "ConversationEntity"
        conversationEntity.managedObjectClassName = "ConversationEntity"
        
        let idAttr = NSAttributeDescription()
        idAttr.name = "id"
        idAttr.attributeType = .stringAttributeType
        idAttr.isOptional = false
        
        let titleAttr = NSAttributeDescription()
        titleAttr.name = "title"
        titleAttr.attributeType = .stringAttributeType
        titleAttr.isOptional = false
        
        conversationEntity.properties = [idAttr, titleAttr]
        
        let stepEntity = NSEntityDescription()
        stepEntity.name = "StepEntity"
        stepEntity.managedObjectClassName = "StepEntity"
        
        let stepIdAttr = NSAttributeDescription()
        stepIdAttr.name = "id"
        stepIdAttr.attributeType = .stringAttributeType
        stepIdAttr.isOptional = false
        
        let textAttr = NSAttributeDescription()
        textAttr.name = "text"
        textAttr.attributeType = .stringAttributeType
        textAttr.isOptional = false
        
        let cidAttr = NSAttributeDescription()
        cidAttr.name = "conversationId"
        cidAttr.attributeType = .stringAttributeType
        cidAttr.isOptional = false
        
        stepEntity.properties = [stepIdAttr, textAttr, cidAttr]
        
        model.entities = [conversationEntity, stepEntity]
        
        container = NSPersistentContainer(name: "Antimatter", managedObjectModel: model)
        if inMemory {
            container.persistentStoreDescriptions.first!.url = URL(fileURLWithPath: "/dev/null")
        }
        container.loadPersistentStores { (storeDescription, error) in
            if let error = error as NSError? {
                fatalError("Unresolved error \(error), \(error.userInfo)")
            }
        }
    }
}

@objc(ConversationEntity)
public class ConversationEntity: NSManagedObject, Identifiable {
    @NSManaged public var id: String
    @NSManaged public var title: String
}

@objc(StepEntity)
public class StepEntity: NSManagedObject, Identifiable {
    @NSManaged public var id: String
    @NSManaged public var text: String
    @NSManaged public var conversationId: String
}
