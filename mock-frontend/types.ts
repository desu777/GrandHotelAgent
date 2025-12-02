
export interface Message {
  id: string;
  role: 'user' | 'model';
  text: string;
  timestamp: number;
}

export enum ChatModel {
  CONCIERGE = 'Grand Concierge',
  BOOKING = 'Asystent Rezerwacji',
}
