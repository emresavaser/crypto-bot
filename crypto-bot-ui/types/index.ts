export interface Trade {
  id: string;
  type: 'buy' | 'sell';
  coin: string;
  amount: number;
  price: number;
  total: number;
  timestamp: Date;
  status: 'completed' | 'pending' | 'failed';
}

export interface Balance {
  coin: string;
  amount: number;
  valueUSD: number;
}

export interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}
