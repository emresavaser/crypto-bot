import { NextRequest, NextResponse } from 'next/server';

const API_BRIDGE_URL = process.env.API_BRIDGE_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { symbol, side, type, quantity, price } = body;

    if (!symbol || !side || !quantity) {
      return NextResponse.json(
        { error: 'Missing required fields: symbol, side, quantity' },
        { status: 400 }
      );
    }

    // API Bridge'e istek gönder
    const response = await fetch(`${API_BRIDGE_URL}/api/trade`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        symbol: symbol,
        side: side.toUpperCase(),
        amount: parseFloat(quantity),
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || data.message || 'Trade failed');
    }

    return NextResponse.json({
      success: true,
      order: {
        orderId: data.order?.id,
        symbol: data.order?.symbol,
        side: data.order?.side,
        type: type || 'MARKET',
        quantity: data.order?.amount,
        price: data.order?.price,
        status: data.order?.status,
      },
    });
  } catch (error) {
    console.error('Trade error:', error);
    return NextResponse.json(
      { error: 'Trade failed', message: (error as Error).message },
      { status: 500 }
    );
  }
}
