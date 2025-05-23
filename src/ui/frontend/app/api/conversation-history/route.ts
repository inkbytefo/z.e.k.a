import { NextResponse } from 'next/server';

/**
 * GET /api/conversation-history
 * 
 * Kullanıcının sohbet geçmişini getirir
 */
export async function GET(request: Request) {
  try {
    // URL'den parametreleri al
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get('limit') || '10';
    
    // Backend API'ye istek gönder
    const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/api/conversation-history?limit=${limit}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'User-ID': 'default_user', // Gerçek uygulamada kullanıcı kimliği kullanılmalı
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.message || 'Backend API hatası' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Sohbet geçmişi API hatası:', error);
    return NextResponse.json(
      { error: 'Sunucu hatası' },
      { status: 500 }
    );
  }
}
