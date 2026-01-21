import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const symbol = request.nextUrl.searchParams.get('symbol') || 'BTCUSDT';
  const interval = request.nextUrl.searchParams.get('interval') || '1h';
  const limit = request.nextUrl.searchParams.get('limit') || '100';

  try {
    const response = await fetch(
      `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`
    );

    if (!response.ok) {
      throw new Error('Binance API error');
    }

    const data = await response.json();

    // Transform klines data to candlestick format
    const candles = data.map((kline: (string | number)[]) => ({
      time: Math.floor(Number(kline[0]) / 1000), // Convert ms to seconds
      open: parseFloat(kline[1] as string),
      high: parseFloat(kline[2] as string),
      low: parseFloat(kline[3] as string),
      close: parseFloat(kline[4] as string),
      volume: parseFloat(kline[5] as string),
    }));

    return NextResponse.json(candles);
  } catch (error) {
    console.error('Klines fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch klines' },
      { status: 500 }
    );
  }
}
