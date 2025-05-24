export interface ChatMessage {
  id?: number;
  user_uuid?: string;
  message: string;
  response: string;
  created_at?: string;
  isUser?: boolean; // 사용자 메시지 구분용
}

export interface ChatHistoryResponse {
  success: boolean;
  history: ChatMessage[];
  message?: string;
}

export interface ChatMessageResponse {
  success: boolean;
  response: string;
  message?: string;
}