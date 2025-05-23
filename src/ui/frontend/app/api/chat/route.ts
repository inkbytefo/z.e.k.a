import { NextResponse } from 'next/server';

/**
 * POST /api/chat
 * 
 * Sohbet mesajını Z.E.K.A asistanına gönderir ve yanıt alır
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { message } = body;

    if (!message) {
      return NextResponse.json(
        { error: 'Mesaj içeriği gereklidir' },
        { status: 400 }
      );
    }

    // Backend API'ye istek gönder
    const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        user_id: 'default_user', // Gerçek uygulamada kullanıcı kimliği kullanılmalı
        language: 'tr',
        style: 'friendly'
      }),
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
    console.error('Sohbet API hatası:', error);
    return NextResponse.json(
      { error: 'Sunucu hatası' },
      { status: 500 }
    );
  }
}
