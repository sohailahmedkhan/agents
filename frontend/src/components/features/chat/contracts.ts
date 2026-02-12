export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
}

export interface KommuneOption {
  key: string;
  label: string;
}
