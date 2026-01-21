import { NextRequest, NextResponse } from 'next/server';

const API_BRIDGE_URL = process.env.API_BRIDGE_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const apiKey = request.headers.get('x-api-key');
  const apiSecret = request.headers.get('x-api-secret');
  const isTestnet = request.headers.get('x-testnet') === 'true';

  if (!apiKey || !apiSecret) {
    return NextResponse.json(
      { error: 'API anahtarları gerekli', trades: [] },
      { status: 401 }
    );
  }

  try {
    // API Bridge'den trades al
    const response = await fetch(`${API_BRIDGE_URL}/api/trades`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('API Bridge error');
    }

    const data = await response.json();

    // API Bridge formatını frontend formatına dönüştür
    const trades = (data.trades || []).map((trade: {
      id: string;
      symbol: string;
      side: string;
      amount: number;
      price: number;
      cost: number;
      status: string;
      timestamp: string;
    }) => ({
      id: trade.id,
      symbol: trade.symbol,
      side: trade.side,
      price: trade.price?.toString() || '0',
      qty: trade.amount?.toString() || '0',
      quoteQty: trade.cost?.toString() || '0',
      time: new Date(trade.timestamp).getTime(),
      isMaker: false,
    }));

    return NextResponse.json({
      trades,
      count: data.count || 0,
      total_pnl: data.total_pnl || 0,
    });
  } catch (error) {
    console.error('Trades fetch error:', error);
    return NextResponse.json(
      { error: 'İşlem geçmişi alınamadı', message: (error as Error).message, trades: [] },
      { status: 500 }
    );
  }
}
