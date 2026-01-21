import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

export async function POST(request: NextRequest) {
  try {
    const { apiKey, apiSecret, isTestnet } = await request.json();

    if (!apiKey || !apiSecret) {
      return NextResponse.json(
        { success: false, error: 'API key and secret required' },
        { status: 400 }
      );
    }

    // Binance Futures API URLs
    // Demo Trading testnet endpoint kullanıyor
    const baseUrl = isTestnet
      ? 'https://testnet.binancefuture.com'
      : 'https://fapi.binance.com';

    const timestamp = Date.now();
    const queryString = `timestamp=${timestamp}&recvWindow=10000`;
    const signature = crypto
      .createHmac('sha256', apiSecret)
      .update(queryString)
      .digest('hex');

    // Futures account endpoint
    const response = await fetch(
      `${baseUrl}/fapi/v2/balance?${queryString}&signature=${signature}`,
      {
        headers: {
          'X-MBX-APIKEY': apiKey,
        },
      }
    );

    if (response.ok) {
      const data = await response.json();
      // USDT bakiyesini bul
      const usdtBalance = data.find((b: { asset: string }) => b.asset === 'USDT');
      return NextResponse.json({
        success: true,
        canTrade: true,
        accountType: 'FUTURES',
        balance: usdtBalance ? parseFloat(usdtBalance.balance) : 0,
      });
    } else {
      const error = await response.json();
      console.error('Binance API error:', error);
      return NextResponse.json(
        { success: false, error: error.msg || 'Invalid API credentials' },
        { status: 401 }
      );
    }
  } catch (error) {
    console.error('Auth verify error:', error);
    return NextResponse.json(
      { success: false, error: 'Connection failed' },
      { status: 500 }
    );
  }
}
