import { NextResponse } from 'next/server';
import crypto from 'crypto';

const BASE_URL = process.env.BINANCE_TESTNET === 'true'
  ? 'https://testnet.binance.vision'
  : 'https://api.binance.com';

function sign(queryString: string, secret: string): string {
  return crypto
    .createHmac('sha256', secret)
    .update(queryString)
    .digest('hex');
}

export async function GET() {
  const apiKey = process.env.BINANCE_API_KEY;
  const apiSecret = process.env.BINANCE_API_SECRET;

  if (!apiKey || !apiSecret) {
    // Return mock data if no API keys configured
    return NextResponse.json({
      balances: [
        { asset: 'BTC', free: '0.5234', locked: '0' },
        { asset: 'ETH', free: '4.2000', locked: '0' },
        { asset: 'USDT', free: '10500.00', locked: '0' },
      ],
      mock: true,
    });
  }

  try {
    const timestamp = Date.now();
    const queryString = `timestamp=${timestamp}&recvWindow=5000`;
    const signature = sign(queryString, apiSecret);

    const response = await fetch(
      `${BASE_URL}/api/v3/account?${queryString}&signature=${signature}`,
      {
        headers: {
          'X-MBX-APIKEY': apiKey,
        },
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.msg || 'Binance API error');
    }

    const data = await response.json();

    // Filter balances with non-zero amounts
    const balances = data.balances.filter(
      (b: { asset: string; free: string; locked: string }) =>
        parseFloat(b.free) > 0 || parseFloat(b.locked) > 0
    );

    return NextResponse.json({ balances, mock: false });
  } catch (error) {
    console.error('Balance fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch balance', message: (error as Error).message },
      { status: 500 }
    );
  }
}
