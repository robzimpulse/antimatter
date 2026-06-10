export class ChatStateManager {
  private activeConversationId: string | null = null;
  private currentStepCount: number = 0;
  private generating: boolean = false;

  setActiveConversation(id: string) {
    this.activeConversationId = id;
    this.currentStepCount = 0;
    this.generating = false;
  }

  clearActiveConversation() {
    this.activeConversationId = null;
    this.currentStepCount = 0;
    this.generating = false;
  }

  getActiveConversation(): string | null {
    return this.activeConversationId;
  }

  getStepCount(): number {
    return this.currentStepCount;
  }

  incrementStepCount() {
    this.currentStepCount++;
  }

  resetStepCount() {
    this.currentStepCount = 0;
  }

  setGenerating(isGenerating: boolean) {
    this.generating = isGenerating;
  }

  isGenerating(): boolean {
    return this.generating;
  }
}
