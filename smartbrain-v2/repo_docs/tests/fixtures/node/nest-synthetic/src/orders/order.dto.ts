export enum OrderStatus {
  OPEN = 'OPEN',
  CLOSED = 'CLOSED',
}

export class OrderDto {
  id: string;
  status: OrderStatus;
  lines?: string[];
}
